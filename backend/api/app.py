import io
import os
import threading
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from backend.api.schemas import (
    HistoryRefreshBatchRequest,
    MessageTemplateRequest,
    ScrapeRequest,
    SelectedLeadsRequest,
    SelectedLeadUpdate,
)
from backend.core.logging import logger
from backend.repositories import database
from backend.services.export_service import generate_xlsx
from backend.services.job_store import get_job, init_job
from backend.services.refresh_service import refresh_history_worker, refresh_leads_worker
from backend.services.scrape_service import scrape_worker


def _start_job(worker, *args) -> str:
    job_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    init_job(job_id)
    thread = threading.Thread(target=worker, args=(job_id, *args), daemon=True)
    thread.start()
    return job_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI lifespan startup triggered")
    database.init_db(os.getenv("DB_PATH", "banco.db"))
    try:
        yield
    finally:
        logger.info("FastAPI lifespan shutdown triggered")


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:1420",
            "http://127.0.0.1:1420",
            "tauri://localhost",
            "http://tauri.localhost",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/scrape")
    async def start_scrape(req: ScrapeRequest):
        try:
            logger.info(
                "Frontend requested scrape segmento=%s cidade=%s estado=%s max_results=%s",
                req.segmento,
                req.cidade,
                req.estado,
                req.max_results,
            )
            if req.max_results <= 0:
                logger.warning(
                    "Rejected scrape request with invalid max_results=%s",
                    req.max_results,
                )
                return JSONResponse(
                    {"error": "A quantidade de leads deve ser maior que zero."},
                    status_code=400,
                )

            job_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
            init_job(job_id)
            thread = threading.Thread(
                target=scrape_worker,
                args=(
                    job_id,
                    req.segmento,
                    req.cidade,
                    req.estado,
                    req.max_results,
                    req.prospectador,
                ),
                daemon=True,
            )
            thread.start()
            logger.info("Scraper thread started job_id=%s", job_id)
            return {"job_id": job_id}
        except Exception:
            logger.exception("Failed to start scrape job")
            traceback.print_exc()
            return JSONResponse(
                {"error": "Falha ao iniciar extração. Veja backend.log para detalhes."},
                status_code=500,
            )

    @app.get("/status/{job_id}")
    async def get_status(job_id: str):
        try:
            job = get_job(job_id)
            if job is None:
                logger.warning("Status requested for unknown job_id=%s", job_id)
                return JSONResponse({"error": "Job não encontrado"}, status_code=404)
            return {
                "status": job.get("status"),
                "progress": job.get("progress", 0),
                "total": job.get("total", 0),
                "log": job.get("log", ""),
                "leads_count": len(job.get("leads", [])),
                "leads": job.get("leads", []),
            }
        except Exception:
            logger.exception("Failed to get status for job %s", job_id)
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao consultar status."}, status_code=500)

    @app.get("/download/{job_id}")
    async def download_xlsx(
        job_id: str,
        segmento: str = "",
        cidade: str = "",
        estado: str = "",
        prospectador: str = "",
    ):
        try:
            logger.info("Download requested for job_id=%s", job_id)
            job = get_job(job_id)
            if not job or job.get("status") != "done":
                logger.warning("Download rejected for unfinished or missing job_id=%s", job_id)
                return JSONResponse({"error": "Job não concluído"}, status_code=400)
            xlsx_bytes = generate_xlsx(
                job["leads"],
                segmento,
                cidade,
                estado,
                prospectador,
            )
            filename = (
                f"leads_{segmento.replace(' ', '_')}_{cidade}_"
                f"{datetime.now().strftime('%Y%m%d')}.xlsx"
            )
            return StreamingResponse(
                io.BytesIO(xlsx_bytes),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except Exception:
            logger.exception("Failed to generate XLSX for job %s", job_id)
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao gerar planilha."}, status_code=500)

    @app.get("/", response_class=HTMLResponse)
    async def home():
        try:
            index_path = Path(__file__).resolve().parents[2] / "index.html"
            if index_path.exists():
                return index_path.read_text(encoding="utf-8")
            return "<html><body><h1>Lead Scraper API</h1><p>Backend ativo.</p></body></html>"
        except Exception:
            logger.exception("Failed to serve backend home endpoint")
            traceback.print_exc()
            return JSONResponse(
                {"error": "Falha ao carregar página inicial do backend"},
                status_code=500,
            )

    @app.get("/health")
    async def health():
        return {"ok": True, "db_ready": database.is_db_ready()}

    @app.get("/history")
    async def get_history():
        try:
            logger.info("History requested by frontend")
            return database.list_search_history()
        except Exception:
            logger.exception("Failed to load search history")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao carregar histórico."}, status_code=500)

    @app.get("/history/{history_id}")
    async def get_history_detail(history_id: int):
        try:
            detail = database.get_search_history_detail(history_id)
            if detail is None:
                return JSONResponse({"error": "Histórico não encontrado"}, status_code=404)
            return detail
        except Exception:
            logger.exception("Failed to load history detail id=%s", history_id)
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao carregar histórico."}, status_code=500)

    @app.post("/history/{history_id}/refresh")
    async def refresh_history(history_id: int):
        try:
            detail = database.get_search_history_detail(history_id)
            if detail is None:
                return JSONResponse({"error": "Histórico não encontrado"}, status_code=404)
            job_id = _start_job(refresh_history_worker, history_id)
            return {"job_id": job_id}
        except Exception:
            logger.exception("Failed to start refresh for history id=%s", history_id)
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao iniciar releitura."}, status_code=500)

    @app.post("/history/refresh-batch")
    async def refresh_history_batch(req: HistoryRefreshBatchRequest):
        try:
            if not req.history_ids:
                return JSONResponse({"error": "Selecione ao menos uma prospecção."}, status_code=400)
            job_id = _start_job(refresh_leads_worker, req.history_ids)
            return {"job_id": job_id}
        except Exception:
            logger.exception("Failed to start batch refresh")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao iniciar releitura em lote."}, status_code=500)

    @app.delete("/history/{history_id}")
    async def delete_history(history_id: int):
        try:
            if not database.delete_search_history(history_id):
                return JSONResponse({"error": "Histórico não encontrado"}, status_code=404)
            return {"ok": True}
        except Exception:
            logger.exception("Failed to delete history id=%s", history_id)
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao excluir histórico."}, status_code=500)

    @app.get("/history/{history_id}/download")
    async def download_history_xlsx(history_id: int):
        try:
            detail = database.get_search_history_detail(history_id)
            if detail is None:
                return JSONResponse({"error": "Histórico não encontrado"}, status_code=404)
            xlsx_bytes = generate_xlsx(
                detail["leads"],
                detail.get("keyword", ""),
                detail.get("city", ""),
                detail.get("state", ""),
                detail.get("prospectador", ""),
            )
            filename = (
                f"leads_{detail.get('keyword', 'busca').replace(' ', '_')}_"
                f"{detail.get('city', '')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            )
            return StreamingResponse(
                io.BytesIO(xlsx_bytes),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except Exception:
            logger.exception("Failed to export history id=%s", history_id)
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao gerar planilha."}, status_code=500)

    @app.get("/selected-leads")
    async def get_selected_leads():
        try:
            return database.list_selected_leads()
        except Exception:
            logger.exception("Failed to list selected leads")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao carregar leads selecionados."}, status_code=500)

    @app.post("/selected-leads")
    async def post_selected_leads(req: SelectedLeadsRequest):
        try:
            leads = [lead.model_dump() for lead in req.leads]
            return database.add_selected_leads(leads)
        except Exception:
            logger.exception("Failed to save selected leads")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao salvar leads selecionados."}, status_code=500)

    @app.patch("/selected-leads/{lead_id}")
    async def patch_selected_lead(lead_id: int, req: SelectedLeadUpdate):
        try:
            updated = database.update_selected_lead(lead_id, req.model_dump(exclude_unset=True))
            if updated is None:
                return JSONResponse({"error": "Lead não encontrado"}, status_code=404)
            return updated
        except Exception:
            logger.exception("Failed to update selected lead id=%s", lead_id)
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao atualizar lead."}, status_code=500)

    @app.delete("/selected-leads/{lead_id}")
    async def remove_selected_lead(lead_id: int):
        try:
            if not database.delete_selected_lead(lead_id):
                return JSONResponse({"error": "Lead não encontrado"}, status_code=404)
            return {"ok": True}
        except Exception:
            logger.exception("Failed to delete selected lead id=%s", lead_id)
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao remover lead."}, status_code=500)

    @app.get("/selected-leads/message-template")
    async def get_message_template():
        try:
            return {"template": database.get_message_template()}
        except Exception:
            logger.exception("Failed to load message template")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao carregar template."}, status_code=500)

    @app.put("/selected-leads/message-template")
    async def put_message_template(req: MessageTemplateRequest):
        try:
            return {"template": database.set_message_template(req.template)}
        except Exception:
            logger.exception("Failed to save message template")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao salvar template."}, status_code=500)

    @app.post("/selected-leads/{lead_id}/refresh-message")
    async def refresh_selected_lead_message(lead_id: int, req: MessageTemplateRequest | None = None):
        try:
            template = req.template if req else None
            updated = database.refresh_selected_lead_message(lead_id, template)
            if updated is None:
                return JSONResponse({"error": "Lead não encontrado"}, status_code=404)
            return updated
        except Exception:
            logger.exception("Failed to refresh message for selected lead id=%s", lead_id)
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao atualizar mensagem."}, status_code=500)

    @app.post("/selected-leads/refresh-links")
    async def refresh_selected_links(req: MessageTemplateRequest | None = None):
        try:
            template = req.template if req else None
            leads = database.refresh_selected_links(template)
            return {"template": database.get_message_template(), "leads": leads}
        except Exception:
            logger.exception("Failed to refresh WhatsApp links")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao atualizar links."}, status_code=500)

    return app

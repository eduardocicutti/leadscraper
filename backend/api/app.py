import io
import os
import traceback
import base64
from binascii import Error as ErroBase64
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse

from backend.api.schemas import (
    BackupRestoreRequest,
    HistoryRefreshBatchRequest,
    MessageTemplateRequest,
    ScrapeRequest,
    SegmentTemplateRequest,
    SelectedLeadFilters,
    SelectedLeadsRequest,
    SelectedLeadUpdate,
    SpreadsheetImportRequest,
)
from backend.api.crm_routes import configurarCrm
from backend.api.prospeccao_routes import rotas as rotasProspeccao
from backend.core.logging import logger
from backend.repositories import database
from backend.services.export_service import generate_xlsx
from backend.services.import_service import parse_leads_spreadsheet
from backend.services.job_store import get_job, iniciarJob, respostaJob
from backend.services.refresh_service import refresh_history_worker, refresh_leads_worker
from backend.services.scrape_service import iniciarColeta


ORIGENS_INTERFACE_LOCAL = (
    "http://localhost:1420",
    "http://127.0.0.1:1420",
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI lifespan startup triggered")
    database.init_db(os.getenv("DB_PATH", "banco.db"))
    try:
        yield
    finally:
        logger.info("FastAPI lifespan shutdown triggered")
        database.close_db()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    configurarCrm(app)
    app.include_router(rotasProspeccao)

    @app.middleware("http")
    async def conferirOrigemDaEscrita(
        pedido: Request, prosseguir: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        origem = pedido.headers.get("origin")
        if (
            pedido.method not in {"GET", "HEAD", "OPTIONS"}
            and origem is not None
            and origem not in ORIGENS_INTERFACE_LOCAL
        ):
            mensagem = "Origem não permitida."
            return JSONResponse(
                {
                    "error": mensagem,
                    "code": "ORIGEM_NAO_PERMITIDA",
                    "message": mensagem,
                    "fieldErrors": [],
                    "correlationId": str(uuid4()),
                },
                status_code=403,
            )
        return await prosseguir(pedido)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGENS_INTERFACE_LOCAL,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

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

            job_id = iniciarColeta(
                req.segmento,
                req.cidade,
                req.estado,
                req.max_results,
                req.prospectador,
            )
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
    async def get_status(job_id: str, somenteProgresso: bool = False):
        try:
            job = get_job(job_id)
            if job is None:
                logger.warning("Status requested for unknown job_id=%s", job_id)
                return JSONResponse({"error": "Job não encontrado"}, status_code=404)
            return respostaJob(job, somenteProgresso)
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

    @app.get("/diagnostics")
    async def diagnostics():
        try:
            return database.get_diagnostics()
        except Exception:
            logger.exception("Failed to load diagnostics")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao carregar diagnóstico."}, status_code=500)

    @app.get("/backup")
    async def download_backup():
        try:
            content, filename = database.create_backup_bytes()
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except Exception:
            logger.exception("Failed to create database backup")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao gerar backup."}, status_code=500)

    @app.post("/restore")
    async def restore_backup(req: BackupRestoreRequest):
        try:
            content = base64.b64decode(req.content_base64, validate=True)
            return database.restore_backup_bytes(content, req.filename)
        except (ErroBase64, UnicodeEncodeError):
            return JSONResponse({"error": "Conteúdo do backup inválido."}, status_code=400)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception:
            logger.exception("Failed to restore database backup")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao restaurar backup."}, status_code=500)

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
            job_id = iniciarJob(refresh_history_worker, history_id)
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
            job_id = iniciarJob(refresh_leads_worker, req.history_ids)
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

    @app.post("/selected-leads/import-spreadsheet")
    async def import_selected_leads_spreadsheet(req: SpreadsheetImportRequest):
        try:
            content = base64.b64decode(req.content_base64)
            parsed_leads, parse_meta = parse_leads_spreadsheet(
                req.filename or "leads.xlsx",
                content,
                req.prospectador,
            )
            result = database.import_selected_leads(parsed_leads)
            return {
                **result,
                "rows_read": parse_meta["rows_read"],
                "columns_detected": parse_meta["columns_detected"],
            }
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception:
            logger.exception("Failed to import selected leads from spreadsheet")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao importar planilha."}, status_code=500)

    @app.post("/selected-leads/export")
    async def export_selected_leads(req: SelectedLeadFilters):
        try:
            filters = req.model_dump()
            leads = database.list_filtered_selected_leads(filters)
            xlsx_bytes = generate_xlsx(
                leads,
                req.segmento or "lista_preferencial",
                req.cidade,
                req.estado,
                req.prospectador,
            )
            filename = f"lista_preferencial_{datetime.now().strftime('%Y%m%d')}.xlsx"
            return StreamingResponse(
                io.BytesIO(xlsx_bytes),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except Exception:
            logger.exception("Failed to export selected leads")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao exportar lista preferencial."}, status_code=500)

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
    async def get_message_template(segmento: str = ""):
        try:
            if segmento:
                return {
                    "segmento": segmento,
                    "template": database.get_message_template_for_segment(segmento),
                }
            return {"template": database.get_message_template()}
        except Exception:
            logger.exception("Failed to load message template")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao carregar template."}, status_code=500)

    @app.put("/selected-leads/message-template")
    async def put_message_template(req: MessageTemplateRequest):
        try:
            if req.segmento:
                return {
                    "segmento": req.segmento,
                    "template": database.set_segment_template(req.segmento, req.template),
                }
            return {"template": database.set_message_template(req.template)}
        except Exception:
            logger.exception("Failed to save message template")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao salvar template."}, status_code=500)

    @app.get("/selected-leads/segment-templates")
    async def get_segment_templates():
        try:
            return database.list_segment_templates()
        except Exception:
            logger.exception("Failed to list segment templates")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao carregar templates por segmento."}, status_code=500)

    @app.put("/selected-leads/segment-templates")
    async def put_segment_template(req: SegmentTemplateRequest):
        try:
            template = database.set_segment_template(req.segmento, req.template)
            leads = database.refresh_selected_links()
            return {"segmento": req.segmento, "template": template, "leads": leads}
        except Exception:
            logger.exception("Failed to save segment template")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao salvar template do segmento."}, status_code=500)

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
            if req and req.segmento:
                database.set_segment_template(req.segmento, req.template)
                template = None
            else:
                template = req.template if req else None
            leads = database.refresh_selected_links(template)
            return {"template": database.get_message_template(), "leads": leads}
        except Exception:
            logger.exception("Failed to refresh WhatsApp links")
            traceback.print_exc()
            return JSONResponse({"error": "Falha ao atualizar links."}, status_code=500)

    return app

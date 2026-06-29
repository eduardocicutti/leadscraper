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

from backend.api.schemas import ScrapeRequest
from backend.core.logging import logger
from backend.repositories import database
from backend.services.export_service import generate_xlsx
from backend.services.job_store import get_job, init_job
from backend.services.scrape_service import scrape_worker


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

    return app

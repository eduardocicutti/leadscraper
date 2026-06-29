import os
import threading
import traceback
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from backend.core.logging import logger
from backend.domain.models import Lead, SearchHistory

engine = None
db_lock = threading.Lock()


def init_db(db_path: str) -> None:
    global engine
    try:
        resolved_path = Path(db_path).expanduser().resolve()
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Opening database at %s", resolved_path)
        engine = create_engine(
            f"sqlite:///{resolved_path}",
            connect_args={"check_same_thread": False},
        )
        SQLModel.metadata.create_all(engine)
        logger.info("Database initialized at %s", resolved_path)
    except Exception:
        logger.exception("Failed to initialize database at %s", db_path)
        traceback.print_exc()
        raise


def ensure_db_ready() -> None:
    if engine is None:
        init_db(os.getenv("DB_PATH", "banco.db"))


def is_db_ready() -> bool:
    return engine is not None


def save_search_history(
    job_id: str,
    segmento: str,
    cidade: str,
    estado: str,
    prospectador: str,
) -> int:
    try:
        ensure_db_ready()
        record = SearchHistory(
            keyword=segmento,
            city=cidade,
            state=estado,
            status="running",
            prospectador=prospectador,
        )
        with db_lock:
            with Session(engine) as session:
                session.add(record)
                session.commit()
                session.refresh(record)
                logger.info("Search history created id=%s job_id=%s", record.id, job_id)
                return record.id
    except Exception:
        logger.exception("Failed to save search history for job %s", job_id)
        traceback.print_exc()
        raise


def save_leads_batch(history_id: int, leads: list[dict]) -> None:
    try:
        ensure_db_ready()
        with db_lock:
            with Session(engine) as session:
                history = session.get(SearchHistory, history_id)
                if history is None:
                    logger.warning("Search history id=%s not found while saving leads", history_id)
                    return

                for lead in leads:
                    session.add(
                        Lead(
                            search_history_id=history_id,
                            company_name=lead.get("nome", ""),
                            phone=lead.get("telefone"),
                            is_whatsapp=lead.get("is_whatsapp", False),
                            whatsapp_link=lead.get("whatsapp_link") or None,
                            website=lead.get("site"),
                            address=lead.get("endereco"),
                            rating=lead.get("nota"),
                            review_count=lead.get("avaliacoes"),
                            category=lead.get("categoria"),
                            porte=lead.get("porte"),
                            score=lead.get("score", 0),
                            classificacao=lead.get("classificacao"),
                            maps_url=lead.get("url_maps"),
                        )
                    )

                history.leads_found = len(leads)
                history.status = "done"
                session.add(history)
                session.commit()
                logger.info("Saved %s leads for history id=%s", len(leads), history_id)
    except Exception:
        logger.exception("Failed to save leads for history id=%s", history_id)
        traceback.print_exc()
        raise


def update_search_history_status(history_id: int, status: str, leads_found: int = 0) -> None:
    try:
        ensure_db_ready()
        with db_lock:
            with Session(engine) as session:
                history = session.get(SearchHistory, history_id)
                if history is None:
                    logger.warning("Search history id=%s not found while updating status", history_id)
                    return
                history.status = status
                history.leads_found = leads_found
                session.add(history)
                session.commit()
                logger.info(
                    "Updated history id=%s status=%s leads_found=%s",
                    history_id,
                    status,
                    leads_found,
                )
    except Exception:
        logger.exception("Failed to update history id=%s status=%s", history_id, status)
        traceback.print_exc()
        raise


def list_search_history(limit: int = 50) -> list[dict]:
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            records = session.exec(
                select(SearchHistory).order_by(SearchHistory.created_at.desc()).limit(limit)
            ).all()
            return [record.model_dump() for record in records]

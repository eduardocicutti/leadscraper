import os
import threading
import traceback
from datetime import datetime
from pathlib import Path

from sqlalchemy import or_, text
from sqlmodel import Session, SQLModel, create_engine, select

from backend.core.logging import logger
from backend.domain.models import AppSetting, Lead, SearchHistory, SelectedLead
from backend.domain.whatsapp import (
    DEFAULT_MESSAGE_TEMPLATE,
    build_whatsapp_link,
    phone_digits,
)

engine = None
db_lock = threading.Lock()
MESSAGE_TEMPLATE_KEY = "selected_lead_message_template"


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
        _migrate_schema()
        logger.info("Database initialized at %s", resolved_path)
    except Exception:
        logger.exception("Failed to initialize database at %s", db_path)
        traceback.print_exc()
        raise


def _migrate_schema() -> None:
    if engine is None:
        return
    migrations = [
        ("selectedlead", "segmento", "TEXT"),
        ("selectedlead", "custom_message", "TEXT DEFAULT ''"),
        ("selectedlead", "last_message_updated_at", "DATETIME"),
    ]
    with engine.connect() as conn:
        for table, column, col_type in migrations:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                conn.commit()
            except Exception:
                pass


def _whatsapp_link_for(record: SelectedLead, template: str) -> str:
    if not record.is_whatsapp:
        return ""
    return build_whatsapp_link(
        record.phone,
        record.company_name,
        template,
        record.segmento or record.category or "",
        record.city or "",
        record.state or "",
        record.prospectador or "",
        custom_message=record.custom_message or None,
    )


def ensure_db_ready() -> None:
    if engine is None:
        init_db(os.getenv("DB_PATH", "banco.db"))


def is_db_ready() -> bool:
    return engine is not None


def lead_to_dict(lead: Lead, history: SearchHistory) -> dict:
    return {
        "id": lead.id,
        "history_id": history.id,
        "nome": lead.company_name,
        "categoria": lead.category or history.keyword,
        "nota": lead.rating,
        "avaliacoes": lead.review_count,
        "endereco": lead.address,
        "telefone": lead.phone,
        "is_whatsapp": lead.is_whatsapp,
        "whatsapp_link": lead.whatsapp_link or "",
        "site": lead.website,
        "url_maps": lead.maps_url or "",
        "porte": lead.porte or "",
        "classificacao": lead.classificacao or "",
        "score": lead.score,
        "cidade": history.city,
        "estado": history.state,
        "prospectador": history.prospectador,
    }


def selected_lead_to_dict(lead: SelectedLead) -> dict:
    return {
        "id": lead.id,
        "source_history_id": lead.source_history_id,
        "source_lead_id": lead.source_lead_id,
        "nome": lead.company_name,
        "categoria": lead.category or "",
        "nota": lead.rating,
        "avaliacoes": lead.review_count,
        "endereco": lead.address,
        "telefone": lead.phone,
        "is_whatsapp": lead.is_whatsapp,
        "whatsapp_link": lead.whatsapp_link or "",
        "site": lead.website,
        "url_maps": lead.maps_url or "",
        "porte": lead.porte or "",
        "classificacao": lead.classificacao or "",
        "score": lead.score,
        "cidade": lead.city or "",
        "estado": lead.state or "",
        "segmento": lead.segmento or lead.category or "",
        "prospectador": lead.prospectador or "",
        "notes": lead.notes,
        "custom_message": lead.custom_message or "",
        "last_message_updated_at": (
            lead.last_message_updated_at.isoformat() if lead.last_message_updated_at else None
        ),
        "selected_at": lead.selected_at.isoformat(),
        "updated_at": lead.updated_at.isoformat(),
    }


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


def get_search_history_detail(history_id: int) -> dict | None:
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            history = session.get(SearchHistory, history_id)
            if history is None:
                return None
            leads = session.exec(select(Lead).where(Lead.search_history_id == history_id)).all()
            return {
                **history.model_dump(),
                "leads": [lead_to_dict(lead, history) for lead in leads],
            }


def get_unique_leads_for_histories(history_ids: list[int]) -> list[dict]:
    ensure_db_ready()
    seen: set[str] = set()
    unique: list[dict] = []
    with db_lock:
        with Session(engine) as session:
            for history_id in history_ids:
                history = session.get(SearchHistory, history_id)
                if history is None:
                    continue
                leads = session.exec(
                    select(Lead).where(Lead.search_history_id == history_id)
                ).all()
                for lead in leads:
                    payload = lead_to_dict(lead, history)
                    maps_url = payload.get("url_maps") or ""
                    phone = phone_digits(payload.get("telefone")) or ""
                    name_city = f"{payload.get('nome')}-{payload.get('cidade')}"
                    key = maps_url or phone or name_city
                    if key in seen:
                        continue
                    seen.add(key)
                    unique.append(payload)
    return unique


def update_lead_record(lead_id: int, data: dict) -> None:
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            record = session.get(Lead, lead_id)
            if record is None:
                return
            record.company_name = data.get("nome", record.company_name)
            record.phone = data.get("telefone")
            record.is_whatsapp = bool(data.get("is_whatsapp"))
            record.whatsapp_link = data.get("whatsapp_link") or None
            record.website = data.get("site")
            record.address = data.get("endereco")
            record.rating = data.get("nota")
            record.review_count = data.get("avaliacoes")
            record.category = data.get("categoria")
            record.porte = data.get("porte")
            record.score = int(data.get("score") or 0)
            record.classificacao = data.get("classificacao")
            record.maps_url = data.get("url_maps")
            session.add(record)
            session.commit()


def delete_search_history(history_id: int) -> bool:
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            history = session.get(SearchHistory, history_id)
            if history is None:
                return False
            leads = session.exec(select(Lead).where(Lead.search_history_id == history_id)).all()
            for lead in leads:
                session.delete(lead)
            session.delete(history)
            session.commit()
            return True


def get_message_template() -> str:
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            setting = session.get(AppSetting, MESSAGE_TEMPLATE_KEY)
            if setting is None:
                return DEFAULT_MESSAGE_TEMPLATE
            return setting.value


def set_message_template(template: str) -> str:
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            setting = session.get(AppSetting, MESSAGE_TEMPLATE_KEY)
            if setting is None:
                setting = AppSetting(key=MESSAGE_TEMPLATE_KEY, value=template)
            else:
                setting.value = template
                setting.updated_at = datetime.now()
            session.add(setting)
            session.commit()
            return setting.value


def _existing_selected(
    session: Session,
    maps_url: str | None,
    normalized_phone: str | None,
    company_name: str | None,
    city: str | None,
) -> SelectedLead | None:
    clauses = []
    if maps_url:
        clauses.append(SelectedLead.maps_url == maps_url)
    if normalized_phone:
        clauses.append(SelectedLead.normalized_phone == normalized_phone)
    if company_name and city:
        clauses.append(
            (SelectedLead.company_name == company_name) & (SelectedLead.city == city)
        )
    if not clauses:
        return None
    return session.exec(select(SelectedLead).where(or_(*clauses))).first()


def add_selected_leads(leads: list[dict]) -> list[dict]:
    ensure_db_ready()
    template = get_message_template()
    saved: list[SelectedLead] = []
    with db_lock:
        with Session(engine) as session:
            for item in leads:
                normalized_phone = phone_digits(item.get("telefone")) or None
                maps_url = item.get("url_maps") or None
                record = _existing_selected(
                    session,
                    maps_url,
                    normalized_phone,
                    item.get("nome"),
                    item.get("cidade"),
                )
                if record is None:
                    record = SelectedLead(company_name=item.get("nome") or "")

                record.source_history_id = item.get("history_id") or item.get("source_history_id")
                record.source_lead_id = item.get("id") or item.get("source_lead_id")
                record.company_name = item.get("nome") or record.company_name
                record.phone = item.get("telefone")
                record.normalized_phone = normalized_phone
                record.is_whatsapp = bool(item.get("is_whatsapp"))
                record.website = item.get("site")
                record.address = item.get("endereco")
                record.rating = item.get("nota")
                record.review_count = item.get("avaliacoes")
                record.category = item.get("categoria")
                record.segmento = item.get("categoria") or item.get("segmento")
                record.porte = item.get("porte")
                record.score = int(item.get("score") or 0)
                record.classificacao = item.get("classificacao")
                record.maps_url = maps_url
                record.city = item.get("cidade")
                record.state = item.get("estado")
                record.prospectador = item.get("prospectador")
                record.updated_at = datetime.now()
                record.whatsapp_link = _whatsapp_link_for(record, template)
                if record.whatsapp_link:
                    record.last_message_updated_at = datetime.now()
                session.add(record)
                saved.append(record)
            session.commit()
            for record in saved:
                session.refresh(record)
            return [selected_lead_to_dict(record) for record in saved]


def list_selected_leads() -> list[dict]:
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            records = session.exec(
                select(SelectedLead).order_by(SelectedLead.selected_at.desc())
            ).all()
            return [selected_lead_to_dict(record) for record in records]


def update_selected_lead(lead_id: int, data: dict) -> dict | None:
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            record = session.get(SelectedLead, lead_id)
            if record is None:
                return None
            if "notes" in data and data["notes"] is not None:
                record.notes = data["notes"]
            if "prospectador" in data and data["prospectador"] is not None:
                record.prospectador = data["prospectador"]
            if "custom_message" in data and data["custom_message"] is not None:
                record.custom_message = data["custom_message"]
            record.updated_at = datetime.now()
            session.add(record)
            session.commit()
            session.refresh(record)
            return selected_lead_to_dict(record)


def delete_selected_lead(lead_id: int) -> bool:
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            record = session.get(SelectedLead, lead_id)
            if record is None:
                return False
            session.delete(record)
            session.commit()
            return True


def refresh_selected_links(template: str | None = None) -> list[dict]:
    if template is not None:
        set_message_template(template)
    current_template = get_message_template()
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            records = session.exec(select(SelectedLead)).all()
            now = datetime.now()
            for record in records:
                record.whatsapp_link = _whatsapp_link_for(record, current_template)
                if record.whatsapp_link:
                    record.last_message_updated_at = now
                record.updated_at = now
                session.add(record)
            session.commit()
            for record in records:
                session.refresh(record)
            return [selected_lead_to_dict(record) for record in records]


def refresh_selected_lead_message(lead_id: int, template: str | None = None) -> dict | None:
    if template is not None:
        set_message_template(template)
    current_template = get_message_template()
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            record = session.get(SelectedLead, lead_id)
            if record is None:
                return None
            record.whatsapp_link = _whatsapp_link_for(record, current_template)
            now = datetime.now()
            if record.whatsapp_link:
                record.last_message_updated_at = now
            record.updated_at = now
            session.add(record)
            session.commit()
            session.refresh(record)
            return selected_lead_to_dict(record)
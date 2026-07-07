import os
import threading
import traceback
from datetime import datetime
from pathlib import Path
from difflib import SequenceMatcher
from unicodedata import combining, normalize

from sqlalchemy import event, or_, text
from sqlmodel import Session, SQLModel, create_engine, select

from backend.core.logging import logger
from backend.domain.models import AppSetting, Lead, SearchHistory, SelectedLead
from backend.domain.whatsapp import (
    DEFAULT_MESSAGE_TEMPLATE,
    build_whatsapp_link,
    phone_digits,
)

engine = None
db_file_path: Path | None = None
db_lock = threading.Lock()
MESSAGE_TEMPLATE_KEY = "selected_lead_message_template"
SEGMENT_TEMPLATE_PREFIX = "selected_lead_message_template_segment:"


def init_db(db_path: str) -> None:
    global engine, db_file_path
    try:
        resolved_path = Path(db_path).expanduser().resolve()
        db_file_path = resolved_path
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Opening database at %s", resolved_path)
        engine = create_engine(
            f"sqlite:///{resolved_path}",
            connect_args={"check_same_thread": False},
        )
        event.listen(engine, "connect", _configure_sqlite_connection)
        SQLModel.metadata.create_all(engine)
        _migrate_schema()
        logger.info("Database initialized at %s", resolved_path)
    except Exception:
        logger.exception("Failed to initialize database at %s", db_path)
        traceback.print_exc()
        raise


def _configure_sqlite_connection(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=FULL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def _checkpoint_wal() -> None:
    if engine is None:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA wal_checkpoint(FULL)"))
    except Exception:
        logger.debug("Could not checkpoint SQLite WAL", exc_info=True)


def _migrate_schema() -> None:
    if engine is None:
        return
    migrations = [
        ("selectedlead", "source_history_id", "INTEGER"),
        ("selectedlead", "source_lead_id", "INTEGER"),
        ("selectedlead", "phone", "TEXT"),
        ("selectedlead", "normalized_phone", "TEXT"),
        ("selectedlead", "is_whatsapp", "BOOLEAN DEFAULT 0"),
        ("selectedlead", "whatsapp_link", "TEXT"),
        ("selectedlead", "website", "TEXT"),
        ("selectedlead", "address", "TEXT"),
        ("selectedlead", "rating", "FLOAT"),
        ("selectedlead", "review_count", "INTEGER"),
        ("selectedlead", "category", "TEXT"),
        ("selectedlead", "porte", "TEXT"),
        ("selectedlead", "score", "INTEGER DEFAULT 0"),
        ("selectedlead", "classificacao", "TEXT"),
        ("selectedlead", "maps_url", "TEXT"),
        ("selectedlead", "segmento", "TEXT"),
        ("selectedlead", "city", "TEXT"),
        ("selectedlead", "state", "TEXT"),
        ("selectedlead", "prospectador", "TEXT"),
        ("selectedlead", "notes", "TEXT DEFAULT ''"),
        ("selectedlead", "custom_message", "TEXT DEFAULT ''"),
        ("selectedlead", "last_message_updated_at", "DATETIME"),
        ("selectedlead", "selected_at", "DATETIME"),
        ("selectedlead", "updated_at", "DATETIME"),
    ]
    with engine.connect() as conn:
        for table, column, col_type in migrations:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                conn.commit()
            except Exception:
                pass
        try:
            conn.execute(
                text(
                    """
                    UPDATE selectedlead
                    SET
                        notes = COALESCE(notes, ''),
                        custom_message = COALESCE(custom_message, ''),
                        selected_at = COALESCE(selected_at, CURRENT_TIMESTAMP),
                        updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
                    """
                )
            )
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


def _segment_template_key(segmento: str) -> str:
    return f"{SEGMENT_TEMPLATE_PREFIX}{_normalize_text(segmento)}"


def _matches_selected_filters(lead: SelectedLead, filters: dict | None) -> bool:
    if not filters:
        return True

    segmento = (filters.get("segmento") or "").strip().lower()
    cidade = (filters.get("cidade") or "").strip().lower()
    estado = (filters.get("estado") or "").strip()
    temperatura = (filters.get("temperatura") or "").strip().lower()
    com_whatsapp = (filters.get("com_whatsapp") or "").strip().lower()
    com_site = (filters.get("com_site") or "").strip().lower()
    prospectador = (filters.get("prospectador") or "").strip().lower()

    lead_segmento = (lead.segmento or lead.category or "").lower()
    if segmento and segmento not in lead_segmento:
        return False
    if cidade and cidade not in (lead.city or "").lower():
        return False
    if estado and lead.state != estado:
        return False
    if prospectador and prospectador not in (lead.prospectador or "").lower():
        return False
    if temperatura == "quente" and "Quente" not in (lead.classificacao or ""):
        return False
    if temperatura == "morno" and "Morno" not in (lead.classificacao or ""):
        return False
    if temperatura == "frio" and "Frio" not in (lead.classificacao or ""):
        return False
    if com_whatsapp == "sim" and not lead.is_whatsapp:
        return False
    if com_whatsapp == "nao" and lead.is_whatsapp:
        return False
    if com_site == "sim" and not lead.website:
        return False
    if com_site == "nao" and lead.website:
        return False
    return True


def ensure_db_ready() -> None:
    if engine is None:
        init_db(os.getenv("DB_PATH", "banco.db"))


def is_db_ready() -> bool:
    return engine is not None


def close_db() -> None:
    global engine
    if engine is not None:
        _checkpoint_wal()
        engine.dispose()
        engine = None


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
        "selected_at": lead.selected_at.isoformat() if lead.selected_at else "",
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else "",
    }


def _lead_record_from_payload(history_id: int, lead: dict) -> Lead:
    return Lead(
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
                    session.add(_lead_record_from_payload(history_id, lead))

                history.leads_found = len(leads)
                history.status = "done"
                session.add(history)
                session.commit()
                _checkpoint_wal()
                logger.info("Saved %s leads for history id=%s", len(leads), history_id)
    except Exception:
        logger.exception("Failed to save leads for history id=%s", history_id)
        traceback.print_exc()
        raise


def save_lead_incremental(history_id: int, lead: dict) -> int | None:
    try:
        ensure_db_ready()
        with db_lock:
            with Session(engine) as session:
                history = session.get(SearchHistory, history_id)
                if history is None:
                    logger.warning("Search history id=%s not found while saving lead", history_id)
                    return None

                maps_url = lead.get("url_maps") or None
                normalized_phone = phone_digits(lead.get("telefone")) or None
                clauses = [Lead.search_history_id == history_id]
                duplicate_checks = []
                if maps_url:
                    duplicate_checks.append(Lead.maps_url == maps_url)
                if normalized_phone:
                    duplicate_checks.append(Lead.phone.like(f"%{normalized_phone[-8:]}%"))
                existing = None
                if duplicate_checks:
                    existing = session.exec(
                        select(Lead).where(*clauses).where(or_(*duplicate_checks))
                    ).first()
                if existing is None:
                    existing = _lead_record_from_payload(history_id, lead)
                else:
                    existing.company_name = lead.get("nome", existing.company_name)
                    existing.phone = lead.get("telefone")
                    existing.is_whatsapp = bool(lead.get("is_whatsapp"))
                    existing.whatsapp_link = lead.get("whatsapp_link") or None
                    existing.website = lead.get("site")
                    existing.address = lead.get("endereco")
                    existing.rating = lead.get("nota")
                    existing.review_count = lead.get("avaliacoes")
                    existing.category = lead.get("categoria")
                    existing.porte = lead.get("porte")
                    existing.score = int(lead.get("score") or 0)
                    existing.classificacao = lead.get("classificacao")
                    existing.maps_url = maps_url

                session.add(existing)
                history.leads_found = session.exec(
                    select(Lead).where(Lead.search_history_id == history_id)
                ).all().__len__()
                history.status = "running"
                session.add(history)
                session.commit()
                session.refresh(existing)
                _checkpoint_wal()
                return existing.id
    except Exception:
        logger.exception("Failed to save incremental lead for history id=%s", history_id)
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
                _checkpoint_wal()
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
            _checkpoint_wal()


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


def _template_for_segment_locked(session: Session, segmento: str | None) -> str:
    if segmento:
        setting = session.get(AppSetting, _segment_template_key(segmento))
        if setting is not None and setting.value:
            return setting.value
    global_setting = session.get(AppSetting, MESSAGE_TEMPLATE_KEY)
    return global_setting.value if global_setting is not None else DEFAULT_MESSAGE_TEMPLATE


def get_message_template_for_segment(segmento: str | None = None) -> str:
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            return _template_for_segment_locked(session, segmento)


def list_segment_templates() -> list[dict]:
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            records = session.exec(
                select(AppSetting).where(AppSetting.key.like(f"{SEGMENT_TEMPLATE_PREFIX}%"))
            ).all()
            return [
                {
                    "segmento": record.key.replace(SEGMENT_TEMPLATE_PREFIX, "", 1),
                    "template": record.value,
                    "updated_at": record.updated_at.isoformat(),
                }
                for record in records
            ]


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
            _checkpoint_wal()
            return setting.value


def set_segment_template(segmento: str, template: str) -> str:
    ensure_db_ready()
    key = _segment_template_key(segmento)
    with db_lock:
        with Session(engine) as session:
            setting = session.get(AppSetting, key)
            if setting is None:
                setting = AppSetting(key=key, value=template)
            else:
                setting.value = template
                setting.updated_at = datetime.now()
            session.add(setting)
            session.commit()
            _checkpoint_wal()
            return setting.value


def _normalize_text(value: str | None) -> str:
    text_value = normalize("NFKD", value or "")
    ascii_value = "".join(ch for ch in text_value if not combining(ch))
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in ascii_value)
    stopwords = {
        "ltda", "me", "mei", "eireli", "sa", "s", "a", "grupo", "empresa",
        "comercio", "servicos", "servico", "the", "de", "da", "do", "das", "dos",
    }
    return " ".join(part for part in cleaned.split() if part not in stopwords)


def _selected_duplicate_reason(candidate: dict, existing: SelectedLead) -> str | None:
    candidate_maps = candidate.get("url_maps") or ""
    candidate_phone = phone_digits(candidate.get("telefone")) or ""
    candidate_name = _normalize_text(candidate.get("nome"))
    candidate_city = _normalize_text(candidate.get("cidade"))
    existing_name = _normalize_text(existing.company_name)
    existing_city = _normalize_text(existing.city)

    if candidate_maps and existing.maps_url and candidate_maps == existing.maps_url:
        return "maps_url"
    if candidate_phone and existing.normalized_phone and candidate_phone == existing.normalized_phone:
        return "telefone"
    if candidate_phone and existing.phone:
        existing_phone = phone_digits(existing.phone)
        if len(candidate_phone) >= 8 and candidate_phone[-8:] == existing_phone[-8:]:
            return "telefone"
    if candidate_name and existing_name and candidate_city == existing_city:
        if SequenceMatcher(None, candidate_name, existing_name).ratio() >= 0.88:
            return "nome_cidade"
    return None


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
                template = _template_for_segment_locked(session, record.segmento)
                record.whatsapp_link = _whatsapp_link_for(record, template)
                if record.whatsapp_link:
                    record.last_message_updated_at = datetime.now()
                session.add(record)
                saved.append(record)
            session.commit()
            for record in saved:
                session.refresh(record)
            _checkpoint_wal()
            return [selected_lead_to_dict(record) for record in saved]


def import_selected_leads(leads: list[dict]) -> dict:
    ensure_db_ready()
    imported: list[dict] = []
    skipped: list[dict] = []
    with db_lock:
        with Session(engine) as session:
            existing_records = session.exec(select(SelectedLead)).all()
            for index, item in enumerate(leads, start=1):
                name = (item.get("nome") or "").strip()
                if not name:
                    skipped.append({"row": index, "reason": "sem_nome", "nome": ""})
                    continue

                duplicate = None
                duplicate_reason = None
                for record in existing_records:
                    duplicate_reason = _selected_duplicate_reason(item, record)
                    if duplicate_reason:
                        duplicate = record
                        break
                if duplicate is not None:
                    skipped.append(
                        {
                            "row": index,
                            "reason": duplicate_reason,
                            "nome": name,
                            "existing_id": duplicate.id,
                            "existing_nome": duplicate.company_name,
                        }
                    )
                    continue

                normalized_phone = phone_digits(item.get("telefone")) or None
                record = SelectedLead(company_name=name)
                record.phone = item.get("telefone")
                record.normalized_phone = normalized_phone
                record.is_whatsapp = bool(item.get("is_whatsapp"))
                record.website = item.get("site")
                record.address = item.get("endereco")
                record.rating = item.get("nota")
                record.review_count = item.get("avaliacoes")
                record.category = item.get("categoria")
                record.segmento = item.get("segmento") or item.get("categoria")
                record.porte = item.get("porte")
                record.score = int(item.get("score") or 0)
                record.classificacao = item.get("classificacao")
                record.maps_url = item.get("url_maps") or None
                record.city = item.get("cidade")
                record.state = item.get("estado")
                record.prospectador = item.get("prospectador")
                record.notes = item.get("notes") or "Importado de planilha"
                record.updated_at = datetime.now()
                template = _template_for_segment_locked(session, record.segmento)
                record.whatsapp_link = _whatsapp_link_for(record, template)
                if record.whatsapp_link:
                    record.last_message_updated_at = datetime.now()
                session.add(record)
                session.flush()
                existing_records.append(record)
                imported.append(selected_lead_to_dict(record))
            session.commit()
            _checkpoint_wal()
            for row in imported:
                if row.get("id"):
                    refreshed = session.get(SelectedLead, row["id"])
                    if refreshed is not None:
                        row.update(selected_lead_to_dict(refreshed))
    return {
        "imported_count": len(imported),
        "skipped_count": len(skipped),
        "imported": imported,
        "skipped": skipped,
    }


def list_selected_leads() -> list[dict]:
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            records = session.exec(
                select(SelectedLead).order_by(SelectedLead.selected_at.desc())
            ).all()
            return [selected_lead_to_dict(record) for record in records]


def list_filtered_selected_leads(filters: dict | None = None) -> list[dict]:
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            records = session.exec(
                select(SelectedLead).order_by(SelectedLead.selected_at.desc())
            ).all()
            filtered = [record for record in records if _matches_selected_filters(record, filters)]
            return [selected_lead_to_dict(record) for record in filtered]


def update_selected_lead(lead_id: int, data: dict) -> dict | None:
    ensure_db_ready()
    should_refresh_link = (
        data.get("prospectador") is not None or data.get("custom_message") is not None
    )
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
            now = datetime.now()
            if should_refresh_link:
                current_template = _template_for_segment_locked(session, record.segmento)
                record.whatsapp_link = _whatsapp_link_for(record, current_template)
                if record.whatsapp_link:
                    record.last_message_updated_at = now
            record.updated_at = now
            session.add(record)
            session.commit()
            _checkpoint_wal()
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
            _checkpoint_wal()
            return True


def refresh_selected_links(template: str | None = None) -> list[dict]:
    if template is not None:
        set_message_template(template)
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            records = session.exec(select(SelectedLead)).all()
            now = datetime.now()
            for record in records:
                current_template = _template_for_segment_locked(session, record.segmento)
                record.whatsapp_link = _whatsapp_link_for(record, current_template)
                if record.whatsapp_link:
                    record.last_message_updated_at = now
                record.updated_at = now
                session.add(record)
            session.commit()
            for record in records:
                session.refresh(record)
            _checkpoint_wal()
            return [selected_lead_to_dict(record) for record in records]


def refresh_selected_lead_message(lead_id: int, template: str | None = None) -> dict | None:
    if template is not None:
        set_message_template(template)
    ensure_db_ready()
    with db_lock:
        with Session(engine) as session:
            record = session.get(SelectedLead, lead_id)
            if record is None:
                return None
            current_template = _template_for_segment_locked(session, record.segmento)
            record.whatsapp_link = _whatsapp_link_for(record, current_template)
            now = datetime.now()
            if record.whatsapp_link:
                record.last_message_updated_at = now
            record.updated_at = now
            session.add(record)
            session.commit()
            session.refresh(record)
            _checkpoint_wal()
            return selected_lead_to_dict(record)


def get_diagnostics() -> dict:
    ensure_db_ready()
    db_path = db_file_path
    exists = bool(db_path and db_path.exists())
    size_bytes = db_path.stat().st_size if db_path and exists else 0
    wal_path = Path(f"{db_path}-wal") if db_path else None
    wal_size = wal_path.stat().st_size if wal_path and wal_path.exists() else 0
    with db_lock:
        with Session(engine) as session:
            history_count = len(session.exec(select(SearchHistory)).all())
            lead_count = len(session.exec(select(Lead)).all())
            selected_count = len(session.exec(select(SelectedLead)).all())
            settings_count = len(session.exec(select(AppSetting)).all())
        with engine.connect() as conn:
            journal_mode = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
            synchronous = conn.exec_driver_sql("PRAGMA synchronous").scalar()
            integrity = conn.exec_driver_sql("PRAGMA integrity_check").scalar()
    return {
        "ok": True,
        "db_ready": is_db_ready(),
        "db_path": str(db_path) if db_path else "",
        "db_exists": exists,
        "db_size_bytes": size_bytes,
        "wal_size_bytes": wal_size,
        "journal_mode": journal_mode,
        "synchronous": synchronous,
        "integrity_check": integrity,
        "counts": {
            "history": history_count,
            "leads": lead_count,
            "selected_leads": selected_count,
            "settings": settings_count,
        },
        "db_path_source": "DB_PATH" if os.getenv("DB_PATH") else "default",
    }

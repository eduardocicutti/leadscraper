import traceback

from backend.adapters.browser_factory import create_browser
from backend.core.logging import logger
from backend.domain.whatsapp import phone_digits
from backend.repositories.database import (
    get_unique_leads_for_histories,
    update_lead_record,
)
from backend.scrapers.google_maps import GoogleMapsScraper
from backend.services import job_store


def _dedupe_key(lead: dict) -> str:
    maps_url = lead.get("url_maps") or ""
    phone = phone_digits(lead.get("telefone")) or ""
    if maps_url:
        return f"url:{maps_url}"
    if phone:
        return f"phone:{phone}"
    return f"name:{lead.get('nome')}-{lead.get('cidade')}"


def refresh_history_worker(job_id: str, history_id: int) -> None:
    refresh_leads_worker(job_id, [history_id])


def refresh_leads_worker(job_id: str, history_ids: list[int]) -> None:
    logger.info("Starting refresh job_id=%s history_ids=%s", job_id, history_ids)
    job = job_store.jobs[job_id]
    browser = create_browser()

    def set_error(message: str) -> None:
        job["status"] = "error"
        job["log"] = message
        logger.error("Refresh job %s failed: %s", job_id, message)

    try:
        job["status"] = "running"
        job["log"] = "Carregando leads salvos..."
        leads = get_unique_leads_for_histories(history_ids)
        if not leads:
            set_error("Nenhum lead encontrado para releitura.")
            return

        job["total"] = len(leads)
        job["log"] = "Iniciando navegador..."
        try:
            browser.launch()
        except Exception as exc:
            logger.exception("Failed to initialize browser for refresh job %s", job_id)
            traceback.print_exc()
            set_error(f"Erro ao iniciar navegador: {str(exc)[:180]}")
            return

        scraper = GoogleMapsScraper(browser, job_id)
        updated_leads: list[dict] = []

        for index, lead in enumerate(leads):
            maps_url = lead.get("url_maps")
            if not maps_url:
                job["log"] = f"Pulando {index + 1}/{len(leads)}: sem URL do Maps"
                job["progress"] = index + 1
                continue

            try:
                refreshed = scraper.extract_lead(
                    maps_url,
                    lead.get("categoria") or lead.get("segmento") or "",
                    lead.get("cidade") or "",
                    lead.get("estado") or "",
                    lead.get("prospectador") or "",
                )
                refreshed["id"] = lead.get("id")
                refreshed["history_id"] = lead.get("history_id")
                update_lead_record(lead["id"], refreshed)
                updated_leads.append(refreshed)
                job["leads"] = sorted(updated_leads, key=lambda item: item["score"], reverse=True)
                job["progress"] = index + 1
                job["log"] = f"Relendo {index + 1}/{len(leads)}: {refreshed['nome']}"
            except Exception as exc:
                logger.exception(
                    "Failed to refresh lead %s/%s for job %s",
                    index + 1,
                    len(leads),
                    job_id,
                )
                traceback.print_exc()
                job["log"] = f"Pulando lead {index + 1}: {str(exc)[:80]}"
                job["progress"] = index + 1
                continue

        if updated_leads:
            job["status"] = "done"
            job["log"] = f"Releitura concluída! {len(updated_leads)} leads atualizados."
            logger.info("Refresh job %s completed with %s leads", job_id, len(updated_leads))
        else:
            set_error("Nenhum lead foi atualizado.")

    except Exception as exc:
        logger.exception("Unexpected refresh failure for job %s", job_id)
        traceback.print_exc()
        set_error(f"Erro: {str(exc)[:180]}")
    finally:
        browser.close()

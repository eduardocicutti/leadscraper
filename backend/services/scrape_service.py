import traceback

from backend.adapters.selenium_browser import create_selenium_browser
from backend.core.logging import logger
from backend.repositories.database import (
    save_leads_batch,
    save_search_history,
    update_search_history_status,
)
from backend.scrapers.google_maps import GoogleMapsScraper
from backend.services import job_store


def scrape_worker(
    job_id: str,
    segmento: str,
    cidade: str,
    estado: str,
    max_results: int,
    prospectador: str,
) -> None:
    logger.info(
        "Starting scraper job_id=%s segmento=%s cidade=%s estado=%s max_results=%s",
        job_id,
        segmento,
        cidade,
        estado,
        max_results,
    )
    history_id: int | None = None
    browser = create_selenium_browser()
    leads: list[dict] = []
    job = job_store.jobs[job_id]

    def set_error(message: str) -> None:
        job["status"] = "error"
        job["log"] = message
        logger.error("Job %s failed: %s", job_id, message)

    try:
        job["status"] = "running"
        job["log"] = "Iniciando Edge..."
        history_id = save_search_history(job_id, segmento, cidade, estado, prospectador)

        try:
            logger.info("Initializing browser for job %s", job_id)
            browser.launch()
        except Exception as exc:
            logger.exception("Failed to initialize browser for job %s", job_id)
            traceback.print_exc()
            set_error(f"Erro ao iniciar Edge: {str(exc)[:180]}")
            if history_id is not None:
                update_search_history_status(history_id, "error")
            return

        scraper = GoogleMapsScraper(browser, job_id)
        query = f"{segmento} em {cidade} {estado}"
        job["log"] = f"Abrindo Google Maps: {query}"

        job["log"] = "Carregando resultados..."
        place_urls = scraper.collect_place_urls(segmento, cidade, estado, max_results)

        job["total"] = len(place_urls)
        job["log"] = f"Encontrou {len(place_urls)} estabelecimentos. Extraindo detalhes..."

        for index, place_url in enumerate(place_urls):
            try:
                lead = scraper.extract_lead(
                    place_url,
                    segmento,
                    cidade,
                    estado,
                    prospectador,
                )
                leads.append(lead)
                job["leads"] = sorted(leads, key=lambda item: item["score"], reverse=True)
                job["progress"] = index + 1
                job["log"] = f"Extraindo {index + 1}/{len(place_urls)}: {lead['nome']}"
            except Exception as exc:
                logger.exception(
                    "Failed to extract lead %s/%s for job %s",
                    index + 1,
                    len(place_urls),
                    job_id,
                )
                traceback.print_exc()
                job["log"] = f"Pulando lead {index + 1}: {str(exc)[:80]}"
                continue

        if leads:
            job["leads"] = sorted(leads, key=lambda item: item["score"], reverse=True)
            job["status"] = "done"
            job["log"] = f"Concluído! {len(leads)} leads coletados."
            if history_id is not None:
                save_leads_batch(history_id, job["leads"])
            logger.info("Job %s completed with %s leads", job_id, len(leads))
        else:
            set_error("Nenhum lead encontrado. Tente outro segmento ou cidade.")
            if history_id is not None:
                update_search_history_status(history_id, "error", 0)

    except Exception as exc:
        logger.exception("Unexpected scraper failure for job %s", job_id)
        traceback.print_exc()
        set_error(f"Erro: {str(exc)[:180]}")
        if history_id is not None:
            update_search_history_status(
                history_id,
                "error",
                len(job.get("leads", leads)),
            )
    finally:
        browser.close()

import re
import time
import traceback

from backend.core.logging import logger
from backend.domain.scoring import classify_porte, score_lead
from backend.domain.whatsapp import build_whatsapp_link
from backend.repositories.database import (
    save_leads_batch,
    save_search_history,
    update_search_history_status,
)
from backend.services import job_store


def scrape_worker(
    job_id: str,
    segmento: str,
    cidade: str,
    estado: str,
    max_results: int,
    prospectador: str,
) -> None:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.edge.service import Service
    from webdriver_manager.microsoft import EdgeChromiumDriverManager

    logger.info(
        "Starting scraper job_id=%s segmento=%s cidade=%s estado=%s max_results=%s",
        job_id,
        segmento,
        cidade,
        estado,
        max_results,
    )
    history_id: int | None = None
    driver = None
    leads: list[dict] = []
    job = job_store.jobs[job_id]

    def set_error(message: str) -> None:
        job["status"] = "error"
        job["log"] = message
        logger.error("Job %s failed: %s", job_id, message)

    def find_text(default: str | None, description: str, callback):
        try:
            return callback()
        except Exception as exc:
            logger.debug(
                "Could not extract %s for job %s: %s",
                description,
                job_id,
                exc,
                exc_info=True,
            )
            return default

    try:
        job["status"] = "running"
        job["log"] = "Iniciando Edge..."
        history_id = save_search_history(job_id, segmento, cidade, estado, prospectador)

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280,900")
        options.add_argument("--lang=pt-BR")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )

        try:
            logger.info("Initializing Edge webdriver for job %s", job_id)
            driver = webdriver.Edge(
                service=Service(EdgeChromiumDriverManager().install()),
                options=options,
            )
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
        except Exception as exc:
            logger.exception("Failed to initialize Edge webdriver for job %s", job_id)
            traceback.print_exc()
            set_error(f"Erro ao iniciar Edge: {str(exc)[:180]}")
            if history_id is not None:
                update_search_history_status(history_id, "error")
            return

        query = f"{segmento} em {cidade} {estado}"
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        job["log"] = f"Abrindo Google Maps: {query}"
        logger.info("Opening Google Maps for job %s: %s", job_id, query)
        driver.get(url)
        time.sleep(4)

        job["log"] = "Carregando resultados..."
        for attempt in range(6):
            try:
                panel = driver.find_element(By.CSS_SELECTOR, '[role="feed"]')
                driver.execute_script("arguments[0].scrollBy(0, 1000)", panel)
                time.sleep(1.5)
            except Exception as exc:
                logger.warning(
                    "Could not scroll results panel on attempt %s for job %s: %s",
                    attempt + 1,
                    job_id,
                    exc,
                )
                break

        cards = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
        hrefs: list[str] = []
        seen: set[str] = set()
        for card in cards:
            try:
                href = card.get_attribute("href")
            except Exception as exc:
                logger.debug(
                    "Could not read maps card href for job %s: %s",
                    job_id,
                    exc,
                    exc_info=True,
                )
                continue
            if href and href not in seen and "/maps/place/" in href:
                seen.add(href)
                hrefs.append(href)
            if len(hrefs) >= max_results:
                break

        job["total"] = len(hrefs)
        job["log"] = f"Encontrou {len(hrefs)} estabelecimentos. Extraindo detalhes..."
        logger.info("Job %s found %s candidate URLs", job_id, len(hrefs))

        for i, href in enumerate(hrefs):
            try:
                driver.get(href)
                time.sleep(2.5)

                nome = find_text(
                    driver.title.replace(" - Google Maps", "").strip(),
                    "company name",
                    lambda: driver.find_element(By.CSS_SELECTOR, "h1").text.strip(),
                )

                nota = find_text(
                    None,
                    "rating",
                    lambda: float(
                        driver.find_element(
                            By.CSS_SELECTOR,
                            'div[jsaction*="pane.rating"] span[aria-hidden="true"]',
                        )
                        .text.replace(",", ".")
                    ),
                )
                if nota is None:

                    def rating_from_aria():
                        el = driver.find_element(
                            By.CSS_SELECTOR, 'span[aria-label*="estrela"]'
                        )
                        match = re.search(
                            r"(\d[.,]\d)", el.get_attribute("aria-label") or ""
                        )
                        return float(match.group(1).replace(",", ".")) if match else None

                    nota = find_text(None, "rating aria-label", rating_from_aria)

                def reviews_from_button():
                    el = driver.find_element(
                        By.CSS_SELECTOR,
                        'button[jsaction*="pane.rating.moreReviews"] span',
                    )
                    nums = re.findall(r"\d+", el.text.replace(".", "").replace(",", ""))
                    return int(nums[0]) if nums else None

                avaliacoes = find_text(None, "review count", reviews_from_button)
                if avaliacoes is None:

                    def reviews_from_text():
                        el = driver.find_element(
                            By.XPATH,
                            '//span[contains(text(),"avaliações") or contains(text(),"avaliação")]',
                        )
                        nums = re.findall(r"\d+", el.text.replace(".", "").replace(",", ""))
                        return int(nums[0]) if nums else None

                    avaliacoes = find_text(None, "review count text", reviews_from_text)

                endereco = find_text(
                    None,
                    "address",
                    lambda: driver.find_element(
                        By.CSS_SELECTOR, 'button[data-item-id="address"]'
                    )
                    .get_attribute("aria-label")
                    .replace("Endereço: ", ""),
                )
                if endereco is None:
                    endereco = find_text(
                        None,
                        "address tooltip",
                        lambda: driver.find_element(
                            By.XPATH, '//button[@data-tooltip="Copiar endereço"]'
                        ).get_attribute("aria-label"),
                    )

                telefone = find_text(
                    None,
                    "phone",
                    lambda: driver.find_element(
                        By.CSS_SELECTOR, 'button[data-item-id*="phone"]'
                    )
                    .get_attribute("aria-label")
                    .replace("Número de telefone: ", "")
                    .strip(),
                )
                if telefone is None:
                    telefone = find_text(
                        None,
                        "phone aria-label",
                        lambda: driver.find_element(
                            By.XPATH,
                            '//button[contains(@aria-label,"telefone") or contains(@aria-label,"phone")]',
                        )
                        .get_attribute("aria-label")
                        .strip(),
                    )

                is_whatsapp = False
                if telefone:
                    digits = re.sub(r"\D", "", telefone)
                    if len(digits) >= 10:
                        local = digits[-9:] if len(digits) >= 9 else digits
                        is_whatsapp = local.startswith("9")

                site = find_text(
                    None,
                    "website",
                    lambda: driver.find_element(
                        By.CSS_SELECTOR, 'a[data-item-id="authority"]'
                    ).get_attribute("href"),
                )
                if site is None:
                    site = find_text(
                        None,
                        "website aria-label",
                        lambda: driver.find_element(
                            By.XPATH, '//a[contains(@aria-label,"Site")]'
                        ).get_attribute("href"),
                    )

                categoria = find_text(
                    None,
                    "category",
                    lambda: driver.find_element(By.CSS_SELECTOR, "button.DkEaL").text.strip(),
                )

                porte = classify_porte(nome, categoria or segmento, avaliacoes or 0)
                whatsapp_link = build_whatsapp_link(telefone, nome) if is_whatsapp else ""

                lead = {
                    "nome": nome,
                    "categoria": categoria or segmento,
                    "nota": nota,
                    "avaliacoes": avaliacoes,
                    "endereco": endereco,
                    "telefone": telefone,
                    "is_whatsapp": is_whatsapp,
                    "whatsapp_link": whatsapp_link,
                    "site": site,
                    "url_maps": href,
                    "porte": porte,
                    "prospectador": prospectador,
                    "cidade": cidade,
                    "estado": estado,
                }
                classificacao, score = score_lead(lead)
                lead["classificacao"] = classificacao
                lead["score"] = score

                leads.append(lead)
                job["leads"] = sorted(leads, key=lambda item: item["score"], reverse=True)
                job["progress"] = i + 1
                job["log"] = f"Extraindo {i + 1}/{len(hrefs)}: {nome}"

            except Exception as exc:
                logger.exception(
                    "Failed to extract lead %s/%s for job %s",
                    i + 1,
                    len(hrefs),
                    job_id,
                )
                traceback.print_exc()
                job["log"] = f"Pulando lead {i + 1}: {str(exc)[:80]}"
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
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                logger.exception("Failed to close Edge webdriver for job %s", job_id)
                traceback.print_exc()

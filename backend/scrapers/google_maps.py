import re
from collections.abc import Callable
from typing import Any

from backend.core.logging import logger
from backend.domain.scoring import classify_porte, score_lead
from backend.domain.whatsapp import build_whatsapp_link
from backend.ports.browser import BrowserPort

MAPS_PLACE_LINK = 'a[href*="/maps/place/"]'
RESULTS_FEED = '[role="feed"]'
SHORT = 500


class GoogleMapsScraper:
    def __init__(self, browser: BrowserPort, job_id: str) -> None:
        self._browser = browser
        self._job_id = job_id

    def collect_place_urls(self, segmento: str, cidade: str, estado: str, max_results: int) -> list[str]:
        query = f"{segmento} em {cidade} {estado}"
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        logger.info("Opening Google Maps for job %s: %s", self._job_id, query)
        self._browser.goto(url)
        if not self._browser.wait_for_selector(RESULTS_FEED, timeout_ms=8000):
            self._browser.wait(1.5)

        hrefs: list[str] = []
        seen: set[str] = set()
        stale_rounds = 0

        for attempt in range(8):
            for href in self._browser.query_all_hrefs(MAPS_PLACE_LINK):
                if href not in seen and "/maps/place/" in href:
                    seen.add(href)
                    hrefs.append(href)
                if len(hrefs) >= max_results:
                    break

            if len(hrefs) >= max_results:
                break

            previous_count = len(hrefs)
            try:
                self._browser.scroll_selector(RESULTS_FEED, 1000)
            except Exception as exc:
                logger.warning(
                    "Could not scroll results panel on attempt %s for job %s: %s",
                    attempt + 1,
                    self._job_id,
                    exc,
                )
                break
            self._browser.wait_for_selector(MAPS_PLACE_LINK, timeout_ms=1500)

            for href in self._browser.query_all_hrefs(MAPS_PLACE_LINK):
                if href not in seen and "/maps/place/" in href:
                    seen.add(href)
                    hrefs.append(href)

            if len(hrefs) == previous_count:
                stale_rounds += 1
                if stale_rounds >= 2:
                    break
            else:
                stale_rounds = 0

            if len(hrefs) >= max_results:
                break

        logger.info("Job %s found %s candidate URLs", self._job_id, len(hrefs))
        return hrefs[:max_results]

    def extract_lead(
        self,
        place_url: str,
        segmento: str,
        cidade: str,
        estado: str,
        prospectador: str,
    ) -> dict:
        self._browser.goto(place_url)
        if not self._browser.wait_for_selector("h1", timeout_ms=5000):
            self._browser.wait(0.8)

        nome = self._safe(
            self._browser.title().replace(" - Google Maps", "").strip(),
            "company name",
            lambda: self._browser.query_text("h1", timeout_ms=SHORT).strip(),
        )

        nota = self._safe(
            None,
            "rating",
            lambda: float(
                self._browser.query_text(
                    'div[jsaction*="pane.rating"] span[aria-hidden="true"]',
                    timeout_ms=SHORT,
                ).replace(",", ".")
            ),
        )
        if nota is None:
            nota = self._safe(
                None,
                "rating aria-label",
                lambda: self._rating_from_aria(),
            )

        avaliacoes = self._safe(None, "review count", lambda: self._reviews_from_button())
        if avaliacoes is None:
            avaliacoes = self._safe(None, "review count text", lambda: self._reviews_from_text())

        endereco = self._safe(
            None,
            "address",
            lambda: self._browser.query_attr(
                'button[data-item-id="address"]', "aria-label", timeout_ms=SHORT
            ).replace("Endereço: ", ""),
        )
        if endereco is None:
            endereco = self._safe(
                None,
                "address tooltip",
                lambda: self._browser.query_attr_xpath(
                    '//button[@data-tooltip="Copiar endereço"]',
                    "aria-label",
                    timeout_ms=SHORT,
                ),
            )

        telefone = self._safe(
            None,
            "phone",
            lambda: self._browser.query_attr(
                'button[data-item-id*="phone"]', "aria-label", timeout_ms=SHORT
            )
            .replace("Número de telefone: ", "")
            .strip(),
        )
        if telefone is None:
            telefone = self._safe(
                None,
                "phone aria-label",
                lambda: self._browser.query_attr_xpath(
                    '//button[contains(@aria-label,"telefone") or contains(@aria-label,"phone")]',
                    "aria-label",
                    timeout_ms=SHORT,
                ).strip(),
            )

        is_whatsapp = self._is_whatsapp(telefone)

        site = self._safe(
            None,
            "website",
            lambda: self._browser.query_attr('a[data-item-id="authority"]', "href", timeout_ms=SHORT),
        )
        if site is None:
            site = self._safe(
                None,
                "website aria-label",
                lambda: self._browser.query_attr_xpath(
                    '//a[contains(@aria-label,"Site")]',
                    "href",
                    timeout_ms=SHORT,
                ),
            )

        categoria = self._safe(
            None,
            "category",
            lambda: self._browser.query_text("button.DkEaL", timeout_ms=SHORT).strip(),
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
            "url_maps": place_url,
            "porte": porte,
            "prospectador": prospectador,
            "cidade": cidade,
            "estado": estado,
        }
        classificacao, score = score_lead(lead)
        lead["classificacao"] = classificacao
        lead["score"] = score
        return lead

    def _rating_from_aria(self) -> float | None:
        aria_label = (
            self._browser.query_attr('span[aria-label*="estrela"]', "aria-label", timeout_ms=SHORT)
            or ""
        )
        match = re.search(r"(\d[.,]\d)", aria_label)
        return float(match.group(1).replace(",", ".")) if match else None

    def _reviews_from_button(self) -> int | None:
        text = self._browser.query_text(
            'button[jsaction*="pane.rating.moreReviews"] span',
            timeout_ms=SHORT,
        )
        nums = re.findall(r"\d+", text.replace(".", "").replace(",", ""))
        return int(nums[0]) if nums else None

    def _reviews_from_text(self) -> int | None:
        text = self._browser.query_text_xpath(
            '//span[contains(text(),"avaliações") or contains(text(),"avaliação")]',
            timeout_ms=SHORT,
        )
        nums = re.findall(r"\d+", text.replace(".", "").replace(",", ""))
        return int(nums[0]) if nums else None

    def _is_whatsapp(self, telefone: str | None) -> bool:
        if not telefone:
            return False
        digits = re.sub(r"\D", "", telefone)
        if len(digits) < 10:
            return False
        local = digits[-9:] if len(digits) >= 9 else digits
        return local.startswith("9")

    def _safe(self, default: Any, description: str, callback: Callable[[], Any]) -> Any:
        try:
            return callback()
        except Exception as exc:
            logger.debug(
                "Could not extract %s for job %s: %s",
                description,
                self._job_id,
                exc,
                exc_info=True,
            )
            return default

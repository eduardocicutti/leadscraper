import os
import traceback

from backend.core.logging import logger
from backend.core.runtime import configure_playwright_path
from backend.ports.browser import BrowserPort

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class PlaywrightBrowser:
    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def launch(self) -> None:
        from playwright.sync_api import sync_playwright

        configure_playwright_path()
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._context = self._browser.new_context(
            locale="pt-BR",
            viewport={"width": 1280, "height": 900},
            user_agent=USER_AGENT,
        )
        self._context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self._page = self._context.new_page()

    def goto(self, url: str) -> None:
        self._require_page().goto(url, wait_until="domcontentloaded")

    def title(self) -> str:
        return self._require_page().title()

    def wait(self, seconds: float) -> None:
        import time

        time.sleep(seconds)

    def scroll_selector(self, selector: str, pixels: int) -> None:
        self._require_page().locator(selector).first.evaluate(
            "(element, amount) => element.scrollBy(0, amount)",
            pixels,
        )

    def query_all_hrefs(self, selector: str) -> list[str]:
        hrefs: list[str] = []
        for locator in self._require_page().locator(selector).all():
            try:
                href = locator.get_attribute("href")
                if href:
                    hrefs.append(href)
            except Exception as exc:
                logger.debug("Could not read href from element: %s", exc, exc_info=True)
        return hrefs

    def query_text(self, selector: str) -> str | None:
        return self._require_page().locator(selector).first.inner_text()

    def query_attr(self, selector: str, attribute: str) -> str | None:
        return self._require_page().locator(selector).first.get_attribute(attribute)

    def query_text_xpath(self, xpath: str) -> str | None:
        return self._require_page().locator(f"xpath={xpath}").first.inner_text()

    def query_attr_xpath(self, xpath: str, attribute: str) -> str | None:
        return self._require_page().locator(f"xpath={xpath}").first.get_attribute(attribute)

    def close(self) -> None:
        try:
            if self._context is not None:
                self._context.close()
            if self._browser is not None:
                self._browser.close()
            if self._playwright is not None:
                self._playwright.stop()
        except Exception:
            logger.exception("Failed to close Playwright browser")
            traceback.print_exc()
        finally:
            self._context = None
            self._browser = None
            self._playwright = None
            self._page = None

    def _require_page(self):
        if self._page is None:
            raise RuntimeError("Browser not launched")
        return self._page


def create_playwright_browser() -> BrowserPort:
    return PlaywrightBrowser()

import traceback

from backend.core.logging import logger
from backend.ports.browser import BrowserPort


class SeleniumBrowser:
    def __init__(self) -> None:
        self._driver = None

    def launch(self) -> None:
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options
        from selenium.webdriver.edge.service import Service
        from webdriver_manager.microsoft import EdgeChromiumDriverManager

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

        self._driver = webdriver.Edge(
            service=Service(EdgeChromiumDriverManager().install()),
            options=options,
        )
        self._driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def goto(self, url: str) -> None:
        self._require_driver().get(url)

    def title(self) -> str:
        return self._require_driver().title

    def wait(self, seconds: float) -> None:
        import time

        time.sleep(seconds)

    def scroll_selector(self, selector: str, pixels: int) -> None:
        from selenium.webdriver.common.by import By

        panel = self._require_driver().find_element(By.CSS_SELECTOR, selector)
        self._require_driver().execute_script(
            "arguments[0].scrollBy(0, arguments[1])",
            panel,
            pixels,
        )

    def query_all_hrefs(self, selector: str) -> list[str]:
        from selenium.webdriver.common.by import By

        elements = self._require_driver().find_elements(By.CSS_SELECTOR, selector)
        hrefs: list[str] = []
        for element in elements:
            try:
                href = element.get_attribute("href")
                if href:
                    hrefs.append(href)
            except Exception as exc:
                logger.debug("Could not read href from element: %s", exc, exc_info=True)
        return hrefs

    def query_text(self, selector: str) -> str | None:
        from selenium.webdriver.common.by import By

        return self._require_driver().find_element(By.CSS_SELECTOR, selector).text

    def query_attr(self, selector: str, attribute: str) -> str | None:
        from selenium.webdriver.common.by import By

        return self._require_driver().find_element(By.CSS_SELECTOR, selector).get_attribute(
            attribute
        )

    def query_text_xpath(self, xpath: str) -> str | None:
        from selenium.webdriver.common.by import By

        return self._require_driver().find_element(By.XPATH, xpath).text

    def query_attr_xpath(self, xpath: str, attribute: str) -> str | None:
        from selenium.webdriver.common.by import By

        return self._require_driver().find_element(By.XPATH, xpath).get_attribute(attribute)

    def close(self) -> None:
        if self._driver is None:
            return
        try:
            self._driver.quit()
        except Exception:
            logger.exception("Failed to close Selenium browser")
            traceback.print_exc()
        finally:
            self._driver = None

    def _require_driver(self):
        if self._driver is None:
            raise RuntimeError("Browser not launched")
        return self._driver


def create_selenium_browser() -> BrowserPort:
    return SeleniumBrowser()

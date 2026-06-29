import os

from backend.ports.browser import BrowserPort


def create_browser() -> BrowserPort:
    engine = os.getenv("BROWSER_ENGINE", "playwright").lower()
    if engine == "selenium":
        from backend.adapters.selenium_browser import SeleniumBrowser

        return SeleniumBrowser()

    from backend.adapters.playwright_browser import PlaywrightBrowser

    return PlaywrightBrowser()

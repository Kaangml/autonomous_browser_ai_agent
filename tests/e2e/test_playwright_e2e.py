import asyncio
import os
from pathlib import Path

import pytest

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:  # pragma: no cover - environment-specific
    PLAYWRIGHT_AVAILABLE = False

from browser.browser_config import BrowserConfig, BrowserConfigManager
from browser.browser import BrowserManager
from browser.actions import BrowserActions
from controller.browser_controller import BrowserController


@pytest.mark.asyncio
@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available in this environment")
async def test_open_page_and_click(tmp_path):
    # prepare config and manager
    config = BrowserConfig(True, {"width": 800, "height": 600}, 10, "test-agent", False)
    manager = BrowserConfigManager(config)

    browser_manager = BrowserManager(config_manager=manager)
    await browser_manager.start()

    actions = BrowserActions(browser_manager)
    # allow file scheme for local fixture files
    controller = BrowserController(actions, allowed_schemes=["http", "https", "file"])

    fixture = Path(__file__).resolve().parent.parent / "fixtures" / "simple_page.html"
    url = f"file://{fixture}"

    # open the page using controller
    res = await controller.execute_action({"type": "goto", "args": {"url": url}})
    assert res["ok"]
    page = res["page"]

    # click the button and extract text
    await controller.execute_action({"type": "click", "args": {"page": page, "selector": "#btn"}})

    # small wait for DOM update
    await asyncio.sleep(0.2)

    ext = await controller.execute_action({"type": "extract_text", "args": {"page": page, "selector": "#result"}})
    assert ext["ok"]
    assert ext["result"] == "Clicked"

    shot = await controller.execute_action({"type": "screenshot", "args": {"page": page, "full_page": True}})
    assert shot["ok"]
    assert isinstance(shot["result"], (bytes, bytearray))

    await browser_manager.close()


@pytest.mark.asyncio
@pytest.mark.skipif(
    not PLAYWRIGHT_AVAILABLE or os.environ.get("RUN_HEADFUL") != "1",
    reason="Run local headful tests with RUN_HEADFUL=1 and Playwright installed",
)
async def test_google_search_headful():
    # This test launches a visible browser (headful). Enable locally with:
    # RUN_HEADFUL=1 pytest tests/e2e/test_playwright_e2e.py::test_google_search_headful -q
    # Use the real Chrome channel (if available) and enable stealth flags to reduce bot detection.
    config = BrowserConfig(False, {"width": 1200, "height": 900}, 30, "test-agent", True, channel="chrome")
    manager = BrowserConfigManager(config)

    browser_manager = BrowserManager(config_manager=manager)
    await browser_manager.start()

    actions = BrowserActions(browser_manager)
    controller = BrowserController(actions, allowed_schemes=["http", "https"])

    # navigate to Google
    res = await controller.execute_action({"type": "goto", "args": {"url": "https://www.google.com"}})
    assert res["ok"]
    page = res["page"]

    # Fill the search box and press Enter
    await page.fill("input[name='q']", "test ok")
    await page.keyboard.press("Enter")

    # Wait for results to appear
    await page.wait_for_selector("#search")

    # Verify title contains search query
    title = await page.title()
    assert "test ok" in title.lower() or "test ok" in (await page.inner_text("#search"))

    await browser_manager.close()

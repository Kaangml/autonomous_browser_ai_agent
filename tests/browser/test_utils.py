import pytest

from browser.utils import BrowserUtils
from playwright.async_api import TimeoutError


class WaitRecorder:
    def __init__(self, should_timeout: bool = False):
        self.calls = []
        self.should_timeout = should_timeout

    async def wait_for_selector(self, selector, **kwargs):
        self.calls.append((selector, kwargs))
        if self.should_timeout:
            raise TimeoutError("timeout")
        return True


@pytest.mark.asyncio
async def test_retry_eventually_returns_value():
    counter = {"attempts": 0}

    async def flaky():
        counter["attempts"] += 1
        if counter["attempts"] < 2:
            raise ValueError("boom")
        return "ok"

    result = await BrowserUtils.retry(flaky, attempts=3, delay=0)

    assert result == "ok"
    assert counter["attempts"] == 2


@pytest.mark.asyncio
async def test_retry_raises_after_exhausting_attempts():
    async def always_fail():
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError):
        await BrowserUtils.retry(always_fail, attempts=2, delay=0)


@pytest.mark.asyncio
async def test_ensure_selector_exists_delegates_to_page():
    page = WaitRecorder()

    await BrowserUtils.ensure_selector_exists(page, "#item", timeout_ms=500)

    assert page.calls[0][0] == "#item"
    assert page.calls[0][1]["timeout"] == 500


@pytest.mark.asyncio
async def test_element_exists_handles_timeout():
    page = WaitRecorder(should_timeout=True)

    exists = await BrowserUtils.element_exists(page, "#missing", timeout_ms=10)

    assert exists is False


def test_normalize_url_adds_scheme():
    assert BrowserUtils.normalize_url("example.com") == "https://example.com"


def test_normalize_file_url_preserved():
    raw = "file:///tmp/test.html"
    assert BrowserUtils.normalize_url(raw) == raw
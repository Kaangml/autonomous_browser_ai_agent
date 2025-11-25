import pytest

from controller.browser_controller import BrowserController


class DummyPage:
    pass


class DummyActions:
    def __init__(self):
        self.last_goto = None

    async def go_to_url(self, url: str):
        self.last_goto = url
        return DummyPage()

    async def click(self, page, selector: str):
        return None

    async def fill(self, page, selector: str, text: str):
        return None

    async def extract_text(self, page, selector: str):
        return "dummy text"

    async def extract_all_links(self, page, selector: str | None = None):
        return ["https://a.local/1"]

    async def screenshot(self, page, full_page: bool = False):
        return b"PNG"


@pytest.mark.asyncio
async def test_execute_action_goto_and_click():
    actions = DummyActions()
    controller = BrowserController(actions)

    goto_res = await controller.execute_action({"type": "goto", "args": {"url": "https://example.com"}})
    assert goto_res["ok"] is True
    assert isinstance(goto_res["page"], DummyPage)

    click_res = await controller.execute_action({"type": "click", "args": {"page": DummyPage(), "selector": "#btn"}})
    assert click_res["ok"] is True


@pytest.mark.asyncio
async def test_execute_sequence_respects_max_steps():
    actions = DummyActions()
    controller = BrowserController(actions)

    steps = [{"type": "goto", "args": {"url": "https://a.test/"}}] * 10

    res = await controller.execute_sequence(steps, max_steps=3)
    assert res["ok"] is False
    assert "max_steps" in res["error"]


@pytest.mark.asyncio
async def test_execute_sequence_detects_loop():
    actions = DummyActions()
    controller = BrowserController(actions)

    # four identical steps should trigger loop detection
    steps = [{"type": "goto", "args": {"url": "https://a.test/"}}] * 4
    res = await controller.execute_sequence(steps, max_steps=10)
    assert res["ok"] is False
    assert "infinite loop" in res["error"]


@pytest.mark.asyncio
async def test_execute_action_disallowed_scheme():
    actions = DummyActions()
    controller = BrowserController(actions, allowed_schemes=["http"])

    res = await controller.execute_action({"type": "goto", "args": {"url": "ftp://files.local/secret"}})
    assert res["ok"] is False
    assert "disallowed url scheme" in res["error"]
import pytest

from controller.browser_controller import BrowserController


class DummyActions:
    def __init__(self):
        self.calls = []

    async def go_to_url(self, url):
        self.calls.append(("goto", url))
        return "page_obj"

    async def click(self, page, selector):
        self.calls.append(("click", selector))

    async def fill(self, page, selector, text):
        self.calls.append(("fill", selector, text))

    async def extract_text(self, page, selector):
        self.calls.append(("extract_text", selector))
        return "some text"

    async def extract_all_links(self, page, selector=None):
        self.calls.append(("links", selector))
        return ["https://a", "https://b"]

    async def screenshot(self, page, full_page=False):
        self.calls.append(("screenshot", full_page))
        return b"PNG"


@pytest.mark.asyncio
async def test_execute_action_goto_and_click():
    da = DummyActions()
    ctrl = BrowserController(da)

    res = await ctrl.execute_action({"type": "goto", "args": {"url": "https://ok.example"}})
    assert res["ok"]
    assert res["result"] == "navigated"

    # click requires a page object in args
    page = object()
    res = await ctrl.execute_action({"type": "click", "args": {"page": page, "selector": "#btn"}})
    assert res["ok"]
    assert res["result"] == "clicked"


@pytest.mark.asyncio
async def test_extract_and_links_and_screenshot():
    da = DummyActions()
    ctrl = BrowserController(da)
    page = object()

    res = await ctrl.execute_action({"type": "extract_text", "args": {"page": page, "selector": "#text"}})
    assert res["ok"] and res["result"] == "some text"

    res = await ctrl.execute_action({"type": "links", "args": {"page": page, "selector": "#container"}})
    assert res["ok"] and isinstance(res["result"], list)

    res = await ctrl.execute_action({"type": "screenshot", "args": {"page": page, "full_page": True}})
    assert res["ok"] and isinstance(res["result"], (bytes, bytearray))


@pytest.mark.asyncio
async def test_disallow_bad_scheme():
    da = DummyActions()
    ctrl = BrowserController(da)

    res = await ctrl.execute_action({"type": "goto", "args": {"url": "file:///etc/passwd"}})
    assert not res["ok"]
    assert "disallowed url scheme" in res["error"]


@pytest.mark.asyncio
async def test_unknown_action():
    da = DummyActions()
    ctrl = BrowserController(da)

    res = await ctrl.execute_action({"type": "unknown_action", "args": {}})
    assert not res["ok"]
    assert "unknown action type" in res["error"]

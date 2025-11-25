"""Utility helpers for browser layer."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Optional, TypeVar
from urllib.parse import urlparse, urlunparse
import random

from playwright.async_api import Page, TimeoutError

T = TypeVar("T")


class BrowserUtils:
    """Reusable helpers for selectors, retries, and normalization."""

    @staticmethod
    async def ensure_selector_exists(page: Page, selector: str, timeout_ms: Optional[int] = None) -> None:
        """Wait until the selector is present on the page."""

        timeout = timeout_ms if timeout_ms is not None else 30_000
        await page.wait_for_selector(selector, timeout=timeout, state="attached")

    @staticmethod
    async def retry(
        func: Callable[[], Awaitable[T]],
        attempts: int = 3,
        delay: float = 0.25,
        exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> T:
        """Retry an async callable a limited number of times."""

        last_error: Optional[Exception] = None
        for attempt in range(1, attempts + 1):
            try:
                return await func()
            except exceptions as exc:  # pragma: no cover - error path monitoring
                last_error = exc
                if attempt == attempts:
                    raise
                await asyncio.sleep(delay)
        raise last_error  # type: ignore[misc]

    @staticmethod
    async def element_exists(page: Page, selector: str, timeout_ms: int = 0) -> bool:
        """Best-effort existence check returning bool instead of raising."""

        try:
            await page.wait_for_selector(selector, timeout=timeout_ms, state="attached")
            return True
        except TimeoutError:
            return False

    @staticmethod
    def normalize_url(raw_url: str) -> str:
        """Ensure URLs have a scheme and are stripped."""

        url = raw_url.strip()
        # Preserve local file URLs as-is (safe for local fixtures)
        if url.lower().startswith("file://"):
            return url

        parsed = urlparse(url, scheme="https")
        # If the parsed result has no network location but some path (e.g. "example.com")
        # only convert to https when the scheme is not 'file' so we don't mangle file paths.
        if parsed.scheme != "file" and not parsed.netloc and parsed.path:
            parsed = urlparse(f"https://{url}")
        if not parsed.scheme:
            parsed = parsed._replace(scheme="https")
        normalized = urlunparse(parsed)
        return normalized

    @staticmethod
    def sanitize_text(raw_text: str) -> str:
        """Normalize whitespace for extracted text."""

        return " ".join(raw_text.split())

    @staticmethod
    def log_action(action_name: str, details: dict | None = None) -> None:
        """Simple stdout logger until proper logging wired in."""

        info = details or {}
        print(f"[BrowserAction] {action_name} -> {info}")

    @staticmethod
    async def human_delay(min_seconds: float = 0.0, max_seconds: float = 0.0) -> None:
        """Sleep for a small random time between min_seconds and max_seconds.

        This helps mimic human pauses and reduce bot-like timing patterns in tests.
        """

        if min_seconds <= 0 and max_seconds <= 0:
            return None
        if max_seconds < min_seconds:
            max_seconds = min_seconds
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)



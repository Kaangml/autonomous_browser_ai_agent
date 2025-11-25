"""Browser configuration management utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from config.settings import Settings


@dataclass(frozen=True)
class BrowserConfig:
    """Immutable representation of browser settings."""

    headless: bool
    viewport: Dict[str, int]
    timeout: int  # seconds
    user_agent: str
    stealth: bool
    channel: str | None = None
    # human-delay in seconds range to add small random pauses for more human-like behavior
    human_delay_min: float = 0.0
    human_delay_max: float = 0.0


class BrowserConfigManager:
    """Loads, validates and converts config values for Playwright."""

    def __init__(self, config: BrowserConfig):
        self.config = config

    @classmethod
    def load_from_settings(cls, settings: Settings | None = None) -> "BrowserConfigManager":
        """Create manager using the global ``Settings`` object."""

        settings = settings or Settings()
        raw_config = {
            "headless": getattr(settings, "BROWSER_HEADLESS", True),
            "viewport": getattr(
                settings,
                "BROWSER_VIEWPORT",
                {"width": 1920, "height": 1080},
            ),
            "timeout": getattr(settings, "BROWSER_TIMEOUT", 30),
            "user_agent": getattr(settings, "BROWSER_USER_AGENT", "Mozilla/5.0"),
            "stealth": getattr(settings, "BROWSER_STEALTH", True),
        }
        validated = cls.validate(raw_config)
        return cls(BrowserConfig(**validated))

    @staticmethod
    def validate(config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user-provided config values."""

        viewport = config_data.get("viewport")
        if not isinstance(viewport, dict):
            raise ValueError("viewport must be a mapping with width/height keys")

        width = int(viewport.get("width", 0))
        height = int(viewport.get("height", 0))
        if width <= 0 or height <= 0:
            raise ValueError("viewport dimensions must be positive integers")

        timeout = int(config_data.get("timeout", 0))
        if timeout <= 0:
            raise ValueError("timeout must be a positive integer")

        user_agent = config_data.get("user_agent")
        if not isinstance(user_agent, str) or not user_agent.strip():
            raise ValueError("user_agent must be a non-empty string")

        validated = {
            "headless": bool(config_data.get("headless", True)),
            "viewport": {"width": width, "height": height},
            "timeout": timeout,
            "user_agent": user_agent.strip(),
            "stealth": bool(config_data.get("stealth", True)),
            "channel": config_data.get("channel"),
            "human_delay_min": float(config_data.get("human_delay_min", 0.0)),
            "human_delay_max": float(config_data.get("human_delay_max", 0.0)),
        }
        return validated

    def to_playwright_options(self) -> Dict[str, Dict[str, Any] | int]:
        """Return launch/context options compatible with Playwright."""

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
        ]

        options = {
            "launch": {
                "headless": self.config.headless,
                "args": launch_args if self.config.stealth else [],
                # allow selecting a specific browser channel (e.g. 'chrome')
                **({"channel": self.config.channel} if self.config.channel else {}),
            },
            "context": {
                "viewport": self.config.viewport,
                "user_agent": self.config.user_agent,
            },
            "timeout": self.config.timeout * 1000,  # convert to ms for Playwright
        }
        return options


# Manuel testing
# manager = BrowserConfigManager.load_from_settings()

# print(f'Manager: {manager}')
# print(f'Manager Config: {manager.config}')

# # Playwright ile kullan:
# options = manager.to_playwright_options()
# print(f'Options: {options}')
"""Main package for autonomous browser agent."""

# Re-exports for convenient importing when package is installed
# These will work when the package is properly installed via pip/uv

__all__ = [
    "Agent",
    "BrowserManager", 
    "BrowserConfigManager",
    "BrowserActions",
    "BrowserController",
]


def __getattr__(name):
    """Lazy imports to avoid circular dependencies and allow flexible usage."""
    if name == "Agent":
        from agent.agent import Agent
        return Agent
    if name == "BrowserManager":
        from browser.browser import BrowserManager
        return BrowserManager
    if name == "BrowserConfigManager":
        from browser.browser_config import BrowserConfigManager
        return BrowserConfigManager
    if name == "BrowserActions":
        from browser.actions import BrowserActions
        return BrowserActions
    if name == "BrowserController":
        from controller.browser_controller import BrowserController
        return BrowserController
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


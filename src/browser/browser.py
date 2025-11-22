from browser_config import BrowserConfig

class Browser:
    """
    Core browser class handling lifecycle: launch, close, restart.
    Uses BrowserConfig for settings.
    """
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.session = None  # Placeholder for actual Playwright or alternative browser session

    def launch(self):
        """
        Launch the browser session.
        """
        pass

    def close(self):
        """
        Close the browser session.
        """
        pass

    def restart(self):
        """
        Restart the browser session (close + launch)
        """
        pass

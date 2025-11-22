class BrowserConfig:
    """
    Placeholder for all browser configuration options.
    This will be used by the Browser class to launch sessions.
    """
    def __init__(self,
                 headless: bool = True,
                 viewport: tuple = (1920, 1080),
                 timeout: int = 30,
                 user_agent: str = "Mozilla/5.0",
                 stealth: bool = True):
        self.headless = headless
        self.viewport = viewport
        self.timeout = timeout
        self.user_agent = user_agent
        self.stealth = stealth

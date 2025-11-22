class BrowserActions:
    """
    Placeholder class for browser actions.
    Each method will interact with the Browser instance.
    """
    def __init__(self, browser):
        self.browser = browser

    def go_to_url(self, url: str):
        """Navigate to a URL"""
        pass

    def click(self, selector: str):
        """Click element by selector"""
        pass

    def fill(self, selector: str, text: str):
        """Fill input element"""
        pass

    def extract_text(self, selector: str):
        """Extract text from element"""
        pass

    def scroll(self, selector: str = None):
        """Scroll page or specific element"""
        pass

    def wait_for(self, selector: str, timeout: int = None):
        """Wait for element to appear"""
        pass

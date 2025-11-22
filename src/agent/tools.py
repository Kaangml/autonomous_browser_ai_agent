class Tools:
    """
    Interface to all external tools agent can use.
    Currently only browser, can extend to APIs, databases, etc.
    """
    def __init__(self, browser):
        self.browser = browser

    def go_to_url(self, url: str):
        """Tool for navigating to a URL"""
        pass

    def click_element(self, selector: str):
        """Tool for clicking element"""
        pass

    def extract_text(self, selector: str):
        """Tool for extracting text"""
        pass

    # Future: add API call tools, database query tools, etc.

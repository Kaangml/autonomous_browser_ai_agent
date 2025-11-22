class Logger:
    """
    Centralized logging for all modules (browser, agent, controller)
    """
    def __init__(self, log_file: str = "system.log"):
        self.log_file = log_file

    def log(self, message: str, level: str = "INFO"):
        """Write log entry with timestamp"""
        print(f"[{level}] {message}")
        # Future: write to file or external logging system

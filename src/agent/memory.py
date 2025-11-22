class Memory:
    """
    Simple short-term memory for agent.
    Can be extended with embeddings or vector DB later.
    """
    def __init__(self):
        self.history = []

    def add_entry(self, entry: dict):
        """Add a new memory entry"""
        self.history.append(entry)

    def get_recent(self, n: int = 5):
        """Return last n entries"""
        return self.history[-n:]

    def search(self, query: str):
        """Search memory for relevant info (placeholder)"""
        pass

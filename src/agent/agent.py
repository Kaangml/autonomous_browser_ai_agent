class Agent:
    """
    Core autonomous agent.
    Receives tasks from controller, decomposes them, executes via browser/tools.
    """
    def __init__(self, name: str = "Agent1"):
        self.name = name
        self.memory = None  # To be connected to memory.py
        self.tools = None   # To be connected to tools.py

    def receive_task(self, task: str):
        """Receive a task in natural language"""
        pass

    def plan_task(self, task: str):
        """
        Decompose task into actionable steps
        """
        pass

    def execute_step(self, step: dict):
        """Execute a single step using available tools/browser"""
        pass

    def evaluate_result(self, step_result: dict):
        """Check if step succeeded, update memory if needed"""
        pass

class PromptTemplates:
    """
    Placeholder for LLM prompt templates for agent reasoning.
    """
    @staticmethod
    def task_decomposition_prompt(task: str) -> str:
        """Return prompt for decomposing task"""
        return f"Decompose this task into steps: {task}"

    @staticmethod
    def step_execution_prompt(step: dict) -> str:
        """Return prompt for executing a step"""
        return f"Execute the following step: {step}"

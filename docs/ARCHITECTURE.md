# 🏗️ Architecture Guide

This document describes the multi-agent architecture of the Autonomous Browser AI Agent.

## Overview

The system uses a **multi-agent architecture** where different AI agents collaborate to accomplish browser automation tasks. Each agent has a specialized role:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER TASK                                     │
│                "Go to Wikipedia and extract the featured article"       │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                                    │
│                                                                         │
│  • Receives high-level task from user                                  │
│  • Coordinates the Plan → Execute → Evaluate loop                      │
│  • Handles retries and re-planning on failures                         │
│  • Decides when task is complete                                       │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    PLANNER      │    │    EXECUTOR     │    │   EVALUATOR     │
│                 │    │                 │    │                 │
│ • Analyzes DOM  │    │ • Runs browser  │    │ • Checks step   │
│ • Creates multi-│    │   actions       │    │   success       │
│   step plan     │    │ • Handles retry │    │ • Detects       │
│ • Uses LLM for  │    │   on failure    │    │   failures      │
│   intelligence  │    │ • Returns       │    │ • Triggers      │
│                 │    │   results       │    │   re-planning   │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         │                      ▼                      │
         │             ┌─────────────────┐             │
         │             │   BROWSER       │             │
         │             │   CONTROLLER    │             │
         │             │                 │             │
         │             │ • Execute action│             │
         │             │ • Safety checks │             │
         │             │ • URL filtering │             │
         │             └────────┬────────┘             │
         │                      │                      │
         │                      ▼                      │
         │             ┌─────────────────┐             │
         └────────────▶│  PLAYWRIGHT     │◀────────────┘
                       │   BROWSER       │
                       │                 │
                       │ • Chromium      │
                       │ • Page actions  │
                       │ • DOM access    │
                       └─────────────────┘
```

## Components

### 1. Orchestrator (`src/agent/orchestrator.py`)

The **Orchestrator** is the main entry point. It coordinates the entire workflow:

```python
class Orchestrator:
    async def execute_task(self, task: str, page: Page = None) -> TaskResult:
        """
        Main loop:
        1. Create plan using Planner
        2. Execute steps using Executor
        3. Evaluate results using Evaluator
        4. Re-plan if needed
        5. Return final result
        """
```

**Key Responsibilities:**
- Initialize and coordinate all agents
- Manage task state (pending, planning, executing, evaluating, complete, failed)
- Handle max retries and max steps limits
- Aggregate execution logs

**Configuration:**
```python
orchestrator = Orchestrator(
    llm=provider,
    planner=planner,
    executor=executor,
    evaluator=evaluator,
    max_retries=3,    # Max re-planning attempts
    max_steps=20,     # Max total steps before giving up
)
```

### 2. Planner (`src/agent/planner.py`)

The **Planner** creates multi-step plans using LLM intelligence:

```python
class PlannerAgent:
    async def plan(
        self,
        task: str,
        page: Page = None,
        page_structure: PageStructure = None,
    ) -> List[Dict[str, Any]]:
        """
        1. Analyze current page DOM (if available)
        2. Generate plan using LLM
        3. Parse plan into executable steps
        4. Fallback to deterministic planner on error
        """
```

**Key Features:**
- **DOM-Aware**: Analyzes page structure to find correct selectors
- **Lookahead**: Plans 3-4 steps ahead considering future states
- **Fallback**: Uses deterministic planner when LLM fails
- **Metadata**: Includes reason, expected outcome, and fallback for each step

**Example Plan Output:**
```python
[
    {
        "type": "goto",
        "args": {"url": "https://wikipedia.org"},
        "metadata": {
            "reason": "Navigate to Wikipedia homepage",
            "expected_outcome": "Page loads with search box visible",
            "fallback": "Try https://en.wikipedia.org"
        }
    },
    {
        "type": "fill",
        "args": {"selector": "#searchInput", "text": "Python programming"},
        "metadata": {
            "reason": "Enter search query",
            "expected_outcome": "Text appears in search box"
        }
    },
    {
        "type": "click",
        "args": {"selector": "#searchButton"},
        "metadata": {
            "reason": "Submit search",
            "expected_outcome": "Navigate to search results"
        }
    }
]
```

### 3. Executor (`src/agent/executor.py`)

The **Executor** runs individual browser actions:

```python
class ExecutorAgent:
    async def execute(
        self,
        step: Dict[str, Any],
        page: Page = None,
    ) -> Dict[str, Any]:
        """
        1. Validate step has required fields
        2. Pre-validate selector exists (optional)
        3. Execute action via BrowserController
        4. Return structured result
        """
    
    async def execute_with_retry(
        self,
        step: Dict[str, Any],
        page: Page = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Execute with automatic retries on failure."""
```

**Key Features:**
- **Validation**: Checks action type and required arguments
- **Retry Logic**: Automatic retries with configurable attempts
- **Error Handling**: Catches exceptions and returns structured errors
- **DOM Analysis**: Optional pre-validation of selectors

### 4. Evaluator (`src/agent/evaluator.py`)

The **Evaluator** assesses step results and decides next actions:

```python
class EvaluatorAgent:
    async def evaluate(
        self,
        step: Dict[str, Any],
        result: Dict[str, Any],
        page: Page = None,
        task: str = "",
        remaining_steps: int = 0,
    ) -> Dict[str, Any]:
        """
        Returns:
        {
            "success": bool,
            "task_complete": bool,
            "should_replan": bool,
            "replan_reason": str,
            "confidence": float
        }
        """
    
    async def check_task_completion(
        self,
        task: str,
        execution_log: list,
    ) -> Dict[str, Any]:
        """Check if overall task is complete."""
```

**Key Features:**
- **Simple Mode**: Rule-based evaluation when no LLM
- **LLM Mode**: Intelligent evaluation with context understanding
- **Re-plan Triggers**: Detects when plan needs adjustment
- **Confidence Scoring**: Indicates certainty of evaluation

### 5. DOM Analyzer (`src/browser/dom_analyzer.py`)

The **DOM Analyzer** extracts page structure for intelligent planning:

```python
class DOMAnalyzer:
    async def analyze(self, page: Page) -> PageStructure:
        """
        Extract:
        - URL, title
        - Interactive elements (buttons, links, inputs)
        - Forms with their fields
        - Main content structure
        """

@dataclass
class PageStructure:
    url: str
    title: str
    elements: List[InteractiveElement]
    forms: List[FormInfo]
    
    def to_prompt_context(self) -> str:
        """Format for LLM prompt."""
```

**Example Output:**
```
URL: https://wikipedia.org
Title: Wikipedia

INTERACTIVE ELEMENTS:
- input#searchInput: text input, name="search"
- button#searchButton: button "Search"
- a.main-link: link "Main Page"

FORMS:
- form#searchform: search form
  - input#searchInput (text)
  - button#searchButton (submit)
```

### 6. Browser Controller (`src/controller/browser_controller.py`)

The **Browser Controller** maps actions to Playwright calls:

```python
class BrowserController:
    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Supported actions:
        - goto: Navigate to URL
        - click: Click element
        - fill: Type into input
        - extract_text: Get element text
        - links: Get all links
        - screenshot: Capture page
        - scroll: Scroll page
        - wait: Wait for element
        """
```

**Safety Features:**
- URL scheme filtering (only http/https allowed)
- Loop detection (prevents infinite action loops)
- Max steps limit
- Timeout handling

### 7. LLM Providers (`src/llm/`)

Abstraction layer for different LLM backends:

```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text completion."""
    
    @abstractmethod
    async def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Generate chat response."""
    
    async def complete_json(self, prompt: str, schema: Dict) -> Dict:
        """Generate JSON response matching schema."""
```

**Available Providers:**
- `GeminiProvider`: Google Gemini (via langchain-google-genai)
- `OpenAIProvider`: OpenAI GPT models (via langchain-openai)
- `BedrockProvider`: AWS Bedrock Claude (via langchain-aws)
- `MockLLMProvider`: For testing without API calls

**Factory Pattern:**
```python
from llm.factory import get_llm_provider, get_provider_for_role

# Auto-detect from environment
provider = get_llm_provider()

# Specific provider
provider = get_llm_provider(LLMProvider.GEMINI)

# Role-based (different models for different agents)
planner_llm = get_provider_for_role("planner")
executor_llm = get_provider_for_role("executor")
```

## Data Flow

### 1. Task Execution Flow

```
User Task → Orchestrator
                │
                ├──▶ Planner.plan(task, page)
                │         │
                │         ▼
                │    [DOM Analysis] ──▶ LLM ──▶ Step List
                │
                ├──▶ For each step:
                │         │
                │         ├──▶ Executor.execute(step, page)
                │         │         │
                │         │         ▼
                │         │    BrowserController ──▶ Playwright
                │         │         │
                │         │         ▼
                │         │    Result {ok, result, error}
                │         │
                │         ├──▶ Evaluator.evaluate(step, result)
                │         │         │
                │         │         ▼
                │         │    {success, task_complete, should_replan}
                │         │
                │         └──▶ If should_replan: goto Planner
                │
                └──▶ TaskResult {success, steps_executed, final_result}
```

### 2. Re-planning Flow

```
Step Failed
    │
    ▼
Evaluator detects failure
    │
    ▼
should_replan = True
    │
    ▼
Orchestrator increments retry_count
    │
    ├──▶ If retry_count < max_retries:
    │         │
    │         ▼
    │    Planner.plan(task, page, executed_steps)
    │         │
    │         ▼
    │    New plan considering what already happened
    │
    └──▶ If retry_count >= max_retries:
              │
              ▼
         TaskResult(success=False, error="Max retries exceeded")
```

## Directory Structure

```
src/
├── agent/
│   ├── __init__.py
│   ├── orchestrator.py    # Main coordinator
│   ├── planner.py         # LLM-based planning
│   ├── executor.py        # Action execution
│   ├── evaluator.py       # Result evaluation
│   ├── agent.py           # Legacy simple agent
│   ├── memory.py          # Short-term memory
│   └── tools.py           # Action definitions
│
├── browser/
│   ├── __init__.py
│   ├── browser.py         # Browser lifecycle
│   ├── browser_config.py  # Configuration
│   ├── actions.py         # High-level actions
│   ├── dom_analyzer.py    # DOM extraction
│   └── utils.py           # Utilities
│
├── controller/
│   ├── __init__.py
│   ├── browser_controller.py  # Action mapping
│   ├── task_manager.py        # Task queue (future)
│   └── workflow.py            # Workflow engine (future)
│
├── llm/
│   ├── __init__.py
│   ├── base.py            # Base provider class
│   ├── factory.py         # Provider factory
│   ├── gemini_provider.py
│   ├── openai_provider.py
│   ├── bedrock_provider.py
│   └── mock_provider.py   # For testing
│
├── config/
│   ├── __init__.py
│   ├── settings.py        # Global settings
│   └── llm_config.py      # LLM configuration
│
└── examples/
    ├── example_wikipedia.py
    ├── example_search.py
    └── example_multiagent.py
```

## Configuration

### Environment Variables

```bash
# LLM Provider
GEMINI_API_KEY=xxx
GEMINI_MODEL=gemini-2.0-flash

# Or OpenAI
OPENAI_API_KEY=xxx
OPENAI_MODEL=gpt-4-turbo

# Or Bedrock
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Role-based providers (optional)
ORCHESTRATOR_PROVIDER=gemini
PLANNER_PROVIDER=gemini
EXECUTOR_PROVIDER=gemini

# Agent settings
MAX_PLANNING_STEPS=10
MAX_RETRIES=3
PLANNING_LOOKAHEAD=4

# Browser settings
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30
```

### Programmatic Configuration

```python
from config.llm_config import LLMConfig, get_llm_config

config = get_llm_config()
print(config.gemini.is_configured)
print(config.get_available_providers())
```

## Extending the System

### Adding a New LLM Provider

1. Create provider class in `src/llm/`:

```python
from llm.base import BaseLLMProvider, LLMResponse, Message

class MyProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "default"):
        self._api_key = api_key
        self._model = model
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        # Implementation
        pass
    
    async def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        # Implementation
        pass
```

2. Add to factory in `src/llm/factory.py`
3. Add configuration in `src/config/llm_config.py`

### Adding a New Browser Action

1. Add method to `src/browser/actions.py`:

```python
class BrowserActions:
    async def my_action(self, page: Page, arg1: str) -> Any:
        # Implementation
        pass
```

2. Add handler in `src/controller/browser_controller.py`:

```python
if typ == "my_action":
    result = await self.browser_actions.my_action(page, args["arg1"])
    return {"ok": True, "result": result}
```

3. Update planner schema in `src/agent/planner.py`

## Testing

The codebase uses pytest with async support:

```bash
# All tests
uv run pytest

# Specific module
uv run pytest tests/agent/

# With coverage
uv run pytest --cov=src

# Verbose
uv run pytest -v
```

Key test files:
- `tests/agent/test_orchestrator.py` - Orchestrator tests
- `tests/agent/test_planner_agent.py` - Planner tests
- `tests/agent/test_executor.py` - Executor tests
- `tests/agent/test_evaluator.py` - Evaluator tests
- `tests/llm/test_mock_provider.py` - Mock provider tests

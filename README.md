# 🤖 Autonomous Browser AI Agent

An intelligent **multi-agent browser automation system** powered by LLMs (Gemini, OpenAI, AWS Bedrock). The agent can understand natural language tasks, plan multi-step browser actions, execute them autonomously, and self-correct when things go wrong.

## ✨ Features

- **Multi-Agent Architecture**: Orchestrator → Planner → Executor → Evaluator loop
- **LLM Integration**: AWS Bedrock (Claude), Google Gemini, OpenAI support
- **DOM-Aware Planning**: Intelligent element detection and selector generation
- **Self-Correction**: Automatic re-planning on failures with retry logic
- **Browser Automation**: Full Playwright integration (navigate, click, fill, extract, screenshot)
- **Safety Controls**: URL scheme filtering, loop detection, max-step limits
- **Human-like Behavior**: Configurable delays to reduce bot detection

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Kaangml/autonomous_browser_ai_agent.git
cd autonomous_browser_ai_agent

# Install dependencies with uv
uv sync

# Install Playwright browsers
uv run playwright install chromium

# Copy environment template and add your API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY (or other provider)
```

### Run Your First Task

```bash
# Simple CLI usage
uv run python -m src --url "https://example.com" --task "extract the page title"

# With visible browser
uv run python -m src --url "https://example.com" --task "extract content" --no-headless

# JSON output
uv run python -m src --url "https://example.com" --task "get the heading" --json
```

### Run Examples

```bash
# Multi-agent example with Gemini
uv run python -m src.examples.example_multiagent

# Wikipedia extraction
uv run python -m src.examples.example_wikipedia

# DuckDuckGo search
uv run python -m src.examples.example_search
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                           │
│         Coordinates the multi-agent workflow                │
│              Plan → Execute → Evaluate                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌────────┐   ┌────────┐   ┌────────────┐
│PLANNER │   │EXECUTOR│   │ EVALUATOR  │
│        │   │        │   │            │
│ - DOM  │   │ - Run  │   │ - Check    │
│   aware│   │   steps│   │   success  │
│ - LLM  │   │ - Retry│   │ - Trigger  │
│   plan │   │   logic│   │   replan   │
└────────┘   └────────┘   └────────────┘
                  │
                  ▼
         ┌───────────────┐
         │   BROWSER     │
         │  CONTROLLER   │
         │               │
         │ - Playwright  │
         │ - Safety      │
         │ - Actions     │
         └───────────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed documentation.

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# LLM Provider (choose one)
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash

# Or OpenAI
# OPENAI_API_KEY=your_key_here
# OPENAI_MODEL=gpt-4-turbo

# Or AWS Bedrock
# AWS_ACCESS_KEY_ID=your_key
# AWS_SECRET_ACCESS_KEY=your_secret
# AWS_REGION=us-east-1
# BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

### Browser Settings

```python
from browser.browser_config import BrowserConfigManager

config = BrowserConfigManager.load_from_settings()
# config.config.headless = False      # Show browser
# config.config.timeout = 30          # Timeout in seconds
# config.config.human_delay_min = 0.5 # Min delay between actions
```

## 📖 Python API

### Using the Multi-Agent System

```python
import asyncio
from dotenv import load_dotenv
load_dotenv()

from llm.factory import get_llm_provider
from agent.planner import PlannerAgent
from agent.executor import ExecutorAgent
from browser.browser import BrowserManager
from browser.browser_config import BrowserConfigManager
from browser.actions import BrowserActions
from controller.browser_controller import BrowserController

async def main():
    # Setup LLM and agents
    llm = get_llm_provider()
    planner = PlannerAgent(llm=llm)
    
    # Setup browser
    config = BrowserConfigManager.load_from_settings()
    browser = BrowserManager(config)
    await browser.start()
    
    actions = BrowserActions(browser)
    controller = BrowserController(actions)
    executor = ExecutorAgent(controller=controller)
    
    try:
        # Plan the task
        steps = await planner.plan("Go to example.com and extract the title")
        print(f"Plan: {len(steps)} steps")
        
        # Execute each step
        page = None
        for step in steps:
            result = await executor.execute(step, page)
            if result.get("page"):
                page = result["page"]
            print(f"{step['type']}: {result.get('ok')}")
            
    finally:
        await browser.close()

asyncio.run(main())
```

### Low-Level Controller Usage

```python
import asyncio
from browser.browser_config import BrowserConfigManager
from browser.browser import BrowserManager
from browser.actions import BrowserActions
from controller.browser_controller import BrowserController

async def main():
    config = BrowserConfigManager.load_from_settings()
    browser = BrowserManager(config)
    await browser.start()
    
    actions = BrowserActions(browser)
    controller = BrowserController(actions)
    
    try:
        # Navigate
        result = await controller.execute_action({
            "type": "goto",
            "args": {"url": "https://example.com"}
        })
        page = result["page"]
        
        # Extract text
        text = await controller.execute_action({
            "type": "extract_text",
            "args": {"page": page, "selector": "h1"}
        })
        print(text["result"])  # "Example Domain"
        
    finally:
        await browser.close()

asyncio.run(main())
```

## 📋 Supported Actions

| Action | Description | Args |
|--------|-------------|------|
| `goto` | Navigate to URL | `url` |
| `click` | Click element | `page`, `selector` |
| `fill` | Type into input | `page`, `selector`, `text` |
| `extract_text` | Get element text | `page`, `selector` |
| `links` | Get all links | `page`, `selector?` |
| `screenshot` | Capture page | `page`, `full_page?` |
| `scroll` | Scroll page | `page`, `selector?` |
| `wait` | Wait for element | `page`, `selector` |

## 🐳 Docker

```bash
# Build the image
docker build -t browser-agent .

# Run with your API key
docker run -e GEMINI_API_KEY=your_key browser-agent \
  --url "https://example.com" --task "extract the title"
```

See [Dockerfile](Dockerfile) for details.

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test module
uv run pytest tests/agent/ -v

# Run with coverage
uv run pytest --cov=src
```

## 📚 Documentation

- [QUICKSTART.md](docs/QUICKSTART.md) - Step-by-step getting started guide
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Detailed system architecture
- [ROADMAP.md](docs/ROADMAP.md) - Development roadmap
- [DEV_NOTES.md](docs/DEV_NOTES.md) - Developer notes

## 🗺️ Roadmap

### Completed ✅
- [x] Multi-agent LLM system (Orchestrator, Planner, Executor, Evaluator)
- [x] LLM provider abstraction (Bedrock, Gemini, OpenAI)
- [x] DOM-aware intelligent planning
- [x] Retry logic and error handling
- [x] Mock provider for testing

### Planned 📋
- [ ] Persistent memory (SQLite/vector DB)
- [ ] Job queue and workflow scheduling
- [ ] Web UI for task management
- [ ] Browser extension integration
- [ ] Multi-tab support

## 📄 License

MIT

## 🤝 Contributing

Contributions welcome! Please read the [ROADMAP.md](docs/ROADMAP.md) first, then open a PR.

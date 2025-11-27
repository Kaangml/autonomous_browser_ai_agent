# 🤖 Autonomous Browser AI Agent

An intelligent browser automation agent built with **Playwright** and a modular **agent-controller-browser** architecture. Plan tasks in natural language, execute them via browser actions, and collect results — all autonomously.

## ✨ Features

- **Browser Automation**: Full Playwright integration (goto, click, fill, extract text, screenshot, etc.)
- **Safety Controls**: URL scheme filtering, loop detection, max-step limits
- **Modular Architecture**: Agent → Controller → Browser layers for testability
- **Human-like Behavior**: Configurable random delays to reduce bot detection
- **CLI & API**: Run from command line or integrate into your Python code
- **Extensible Planner**: Pluggable LLM interface for intelligent task planning

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Kaangml/autonomous_browser_ai_agent.git
cd autonomous_browser_ai_agent

# Install dependencies with uv (recommended)
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

### Run from CLI

```bash
# Extract text from a webpage
uv run python -m src --url "https://example.com" --task "extract the page title"

# Run with visible browser window
uv run python -m src --url "https://example.com" --task "extract the page title" --no-headless

# Output as JSON
uv run python -m src --url "https://example.com" --task "read the main content" --json
```

### Run Examples

```bash
# Wikipedia example: extract featured article
uv run python -m src.examples.example_wikipedia

# DuckDuckGo search example
uv run python -m src.examples.example_search
```

## 📖 Usage in Python

```python
import asyncio
from browser.browser_config import BrowserConfigManager
from browser.browser import BrowserManager
from browser.actions import BrowserActions
from controller.browser_controller import BrowserController

async def main():
    # Setup
    config = BrowserConfigManager()
    config.config.headless = True
    
    browser = BrowserManager(config)
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
        print(text["result"])
        
    finally:
        await browser.close()

asyncio.run(main())
```

## 🏗️ Architecture

```
src/
├── agent/          # Task planning and reasoning
│   ├── agent.py    # Main agent class (plan → execute → reflect)
│   ├── planner.py  # LLM-based task decomposition
│   └── memory.py   # Short-term memory
├── browser/        # Playwright automation layer
│   ├── browser.py  # Browser lifecycle management
│   ├── actions.py  # High-level actions (click, fill, extract, etc.)
│   └── utils.py    # Retry logic, human delays, URL normalization
├── controller/     # Action orchestration
│   └── browser_controller.py  # Maps agent actions to browser calls
├── config/         # Configuration management
└── examples/       # Working examples
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/browser/test_actions.py
```

## 📋 Supported Actions

| Action | Description | Args |
|--------|-------------|------|
| `goto` | Navigate to URL | `url` |
| `click` | Click element | `page`, `selector` |
| `fill` | Type into input | `page`, `selector`, `text` |
| `extract_text` | Get element text | `page`, `selector` |
| `links` | Get all links | `page`, `selector` (optional) |
| `screenshot` | Capture page | `page`, `full_page` (optional) |

## ⚙️ Configuration

Browser behavior can be customized via `BrowserConfigManager`:

```python
config = BrowserConfigManager()
config.config.headless = False          # Show browser window
config.config.timeout = 30              # Timeout in seconds
config.config.viewport_width = 1920     # Browser width
config.config.viewport_height = 1080    # Browser height
config.config.human_delay_min = 0.5     # Min delay between actions
config.config.human_delay_max = 1.5     # Max delay between actions
config.config.channel = "chrome"        # Use Chrome instead of Chromium
```

## 🗺️ Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the development roadmap.

### Planned Features
- [ ] Persistent memory (SQLite/vector DB)
- [ ] Real LLM integration (OpenAI, Anthropic, Bedrock)
- [ ] Job queue and workflow management
- [ ] Retry policies with exponential backoff
- [ ] Structured logging and metrics

## 📄 License

MIT

## 🤝 Contributing

Contributions welcome! Please read the roadmap first, then open a PR.

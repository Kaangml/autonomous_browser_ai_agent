# 🚀 Quick Start Guide

This guide will get you up and running with the Autonomous Browser AI Agent in under 5 minutes.

## Prerequisites

- **Python 3.11+**
- **uv** (Python package manager) - [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **API Key** for at least one LLM provider (Gemini recommended for quick start)

## Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/Kaangml/autonomous_browser_ai_agent.git
cd autonomous_browser_ai_agent

# Install all dependencies
uv sync

# Install Playwright browsers (required for browser automation)
uv run playwright install chromium
```

## Step 2: Configure Your LLM Provider

Copy the environment template:

```bash
cp .env.example .env
```

Edit `.env` and add your API key. The easiest option is **Google Gemini**:

```bash
# .env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
```

### Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key and paste it in `.env`

### Alternative: OpenAI

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo
```

### Alternative: AWS Bedrock

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

## Step 3: Verify Installation

Run the tests to make sure everything is working:

```bash
uv run pytest tests/ -v --tb=short
```

You should see all tests passing (68+ tests).

## Step 4: Run Your First Task

### Option A: CLI

```bash
# Extract text from a webpage
uv run python -m src --url "https://example.com" --task "extract the page title"
```

Expected output:
```
Task: extract the page title
URL: https://example.com
Result: Example Domain
```

### Option B: Python Script

Create a file `my_first_task.py`:

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
    # Initialize LLM
    llm = get_llm_provider()
    print(f"Using LLM: {type(llm).__name__}")
    
    # Create planner and executor
    planner = PlannerAgent(llm=llm)
    
    # Setup browser
    config = BrowserConfigManager.load_from_settings()
    browser = BrowserManager(config)
    await browser.start()
    
    actions = BrowserActions(browser)
    controller = BrowserController(actions)
    executor = ExecutorAgent(controller=controller)
    
    try:
        # Define your task
        task = "Go to wikipedia.org and extract the featured article title"
        print(f"\n📋 Task: {task}")
        
        # Let the LLM plan the steps
        steps = await planner.plan(task)
        print(f"\n🔧 Plan ({len(steps)} steps):")
        for i, step in enumerate(steps, 1):
            print(f"   {i}. {step['type']}: {step['args']}")
        
        # Execute the plan
        print("\n🚀 Executing...")
        page = None
        for step in steps:
            result = await executor.execute(step, page)
            status = "✅" if result.get("ok") else "❌"
            print(f"   {status} {step['type']}")
            
            if result.get("page"):
                page = result["page"]
            
            if result.get("result") and step["type"] == "extract_text":
                print(f"\n📄 Result: {result['result'][:200]}...")
        
        print("\n✅ Done!")
        
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
uv run python my_first_task.py
```

## Step 5: Try More Examples

### Wikipedia Example

```bash
uv run python -m src.examples.example_wikipedia
```

### Search Example

```bash
uv run python -m src.examples.example_search
```

### Multi-Agent Example

```bash
uv run python -m src.examples.example_multiagent
```

## Common Issues

### "GEMINI_API_KEY not configured"

Make sure your `.env` file exists and contains the API key:

```bash
cat .env | grep GEMINI
```

### "Playwright browsers not installed"

Run the install command:

```bash
uv run playwright install chromium
```

### "Import errors"

Make sure you're running from the project root and using `uv run`:

```bash
cd autonomous_browser_ai_agent
uv run python -m src --help
```

### "API key was reported as leaked"

Your API key was exposed (e.g., pushed to GitHub). Generate a new one and update `.env`.

## Next Steps

- 📖 Read the [Architecture Guide](ARCHITECTURE.md) to understand how the system works
- 🔧 Check [ROADMAP.md](ROADMAP.md) for planned features
- 🐳 Try the [Docker setup](../Dockerfile) for containerized deployment
- 🧪 Write your own tasks and explore the capabilities!

## Tips for Writing Good Tasks

✅ **Good tasks:**
- "Go to example.com and extract the main heading"
- "Search Google for 'python tutorial' and get the first 3 result titles"
- "Navigate to wikipedia.org, search for 'artificial intelligence', and extract the first paragraph"

❌ **Too vague:**
- "Get information" (what information? from where?)
- "Do something on this page" (what exactly?)

The more specific your task, the better the LLM can plan the steps!

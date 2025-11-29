"""
Full Orchestrator Example - Showcases the complete multi-agent system.

This is the flagship example that demonstrates ALL components:
- Orchestrator: Coordinates the entire workflow
- PlannerAgent: Creates intelligent step-by-step plans using LLM
- ExecutorAgent: Executes browser actions
- EvaluatorAgent: Validates results and suggests corrections
- Re-planning: Automatically handles failures

The orchestrator implements: Plan → Execute → Evaluate → (Re-plan) loop

Requirements:
- Set GEMINI_API_KEY (or OPENAI_API_KEY, AWS credentials) in .env
- Run: uv run python -m src.examples.example_orchestrator

Author: Autonomous Browser AI Agent Team
"""

import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from llm.factory import get_llm_provider
from agent.orchestrator import Orchestrator, TaskStatus
from agent.planner import PlannerAgent
from agent.executor import ExecutorAgent
from agent.evaluator import EvaluatorAgent
from browser.browser import BrowserManager
from browser.browser_config import BrowserConfigManager, BrowserConfig
from browser.actions import BrowserActions
from browser.dom_analyzer import DOMAnalyzer
from controller.browser_controller import BrowserController


def print_banner():
    """Print a fancy banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║     🤖 AUTONOMOUS BROWSER AI AGENT - ORCHESTRATOR DEMO 🤖     ║
║                                                              ║
║  Multi-Agent System:                                         ║
║  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       ║
║  │  PLANNER    │───▶│  EXECUTOR   │───▶│  EVALUATOR  │       ║
║  │  (LLM)      │    │  (Browser)  │    │  (LLM)      │       ║
║  └─────────────┘    └─────────────┘    └─────────────┘       ║
║         ▲                                    │               ║
║         └────────────────────────────────────┘               ║
║                    RE-PLANNING LOOP                          ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def run_orchestrator_demo():
    """Run the full orchestrator demonstration."""
    
    print_banner()
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 1: Initialize LLM Provider
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "═" * 60)
    print("📦 STEP 1: Initializing LLM Provider")
    print("═" * 60)
    
    try:
        llm = get_llm_provider()
        print(f"   ✅ Provider: {type(llm).__name__}")
        print(f"   ✅ Model: {getattr(llm, '_model', 'default')}")
    except Exception as e:
        print(f"   ❌ Failed to initialize LLM: {e}")
        print("   📝 Make sure you have set an API key in .env file:")
        print("      - GEMINI_API_KEY for Google Gemini")
        print("      - OPENAI_API_KEY for OpenAI")
        print("      - AWS credentials for Bedrock")
        return
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 2: Initialize Browser
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "═" * 60)
    print("🌐 STEP 2: Initializing Browser")
    print("═" * 60)
    
    config = BrowserConfig(
        headless=True,  # Set to False to watch the browser
        viewport={"width": 1280, "height": 720},
        timeout=30,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0",
        stealth=True,
    )
    config_manager = BrowserConfigManager(config)
    browser = BrowserManager(config_manager)
    await browser.start()
    print("   ✅ Browser started (headless mode)")
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 3: Create All Agents
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "═" * 60)
    print("🤖 STEP 3: Creating Agent Team")
    print("═" * 60)
    
    # Controller for browser actions
    actions = BrowserActions(browser)
    controller = BrowserController(actions)
    
    # Create specialized agents
    planner = PlannerAgent(llm=llm)
    print("   ✅ PlannerAgent created (uses LLM for intelligent planning)")
    
    executor = ExecutorAgent(controller=controller)
    print("   ✅ ExecutorAgent created (executes browser actions)")
    
    evaluator = EvaluatorAgent(llm=llm)
    print("   ✅ EvaluatorAgent created (validates results)")
    
    # Create the orchestrator
    orchestrator = Orchestrator(
        llm=llm,
        planner=planner,
        executor=executor,
        evaluator=evaluator,
        max_retries=3,
        max_steps=15,
    )
    print("   ✅ Orchestrator created (coordinates all agents)")
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 4: Define Tasks
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "═" * 60)
    print("📋 STEP 4: Task Definitions")
    print("═" * 60)
    
    # Multiple tasks to demonstrate different capabilities
    tasks = [
        {
            "name": "Simple Navigation & Extraction",
            "description": "Go to example.com and extract the page title and main heading",
        },
        {
            "name": "Search & Navigate",
            "description": "Go to Wikipedia, search for 'Artificial Intelligence', and extract the first paragraph of the article",
        },
        {
            "name": "Multi-step Data Extraction", 
            "description": "Go to Hacker News (news.ycombinator.com) and extract the titles of the top 3 stories",
        },
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n   Task {i}: {task['name']}")
        print(f"   └── {task['description']}")
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 5: Execute Tasks with Orchestrator
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "═" * 60)
    print("🚀 STEP 5: Executing Tasks")
    print("═" * 60)
    
    results = []
    
    for i, task_def in enumerate(tasks, 1):
        print(f"\n{'─' * 60}")
        print(f"🎯 TASK {i}: {task_def['name']}")
        print(f"{'─' * 60}")
        print(f"📝 {task_def['description']}")
        
        start_time = datetime.now()
        
        # Execute using the orchestrator
        result = await orchestrator.execute_task(
            task=task_def["description"],
            page=None,  # Orchestrator will manage the page
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Print result summary
        print(f"\n   📊 Result Summary:")
        print(f"   ├── Success: {'✅ Yes' if result.success else '❌ No'}")
        print(f"   ├── Steps Executed: {result.steps_executed}")
        print(f"   ├── Time: {elapsed:.2f}s")
        
        if result.success and result.final_result:
            print(f"   └── Data Extracted:")
            if isinstance(result.final_result, str):
                # Truncate long results
                display = result.final_result[:200] + "..." if len(result.final_result) > 200 else result.final_result
                print(f"       {display}")
            else:
                print(f"       {result.final_result}")
        elif result.error:
            print(f"   └── Error: {result.error}")
        
        results.append({
            "task": task_def["name"],
            "success": result.success,
            "steps": result.steps_executed,
            "time": elapsed,
        })
        
        # Small delay between tasks
        await asyncio.sleep(1)
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 6: Final Report
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "═" * 60)
    print("📈 FINAL REPORT")
    print("═" * 60)
    
    total_success = sum(1 for r in results if r["success"])
    total_time = sum(r["time"] for r in results)
    
    print(f"""
   ┌────────────────────────────────────────────────┐
   │  Tasks Completed: {total_success}/{len(results)}                          │
   │  Total Time: {total_time:.2f}s                              │
   │  Average Time per Task: {total_time/len(results):.2f}s                    │
   └────────────────────────────────────────────────┘
    """)
    
    print("   Task Breakdown:")
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"   {status} {r['task']}: {r['steps']} steps, {r['time']:.2f}s")
    
    # ═══════════════════════════════════════════════════════════════
    # CLEANUP
    # ═══════════════════════════════════════════════════════════════
    await browser.close()
    print("\n🔒 Browser closed")
    print("\n" + "═" * 60)
    print("✨ Orchestrator Demo Complete!")
    print("═" * 60)


async def run_single_task_demo():
    """Run a simpler single-task demo for quick testing."""
    
    print("\n🚀 Quick Single-Task Demo")
    print("=" * 50)
    
    # Initialize
    llm = get_llm_provider()
    
    config = BrowserConfig(
        headless=True,
        viewport={"width": 1280, "height": 720},
        timeout=30,
        user_agent="Mozilla/5.0",
        stealth=True,
    )
    browser = BrowserManager(BrowserConfigManager(config))
    await browser.start()
    
    # Create agents
    actions = BrowserActions(browser)
    controller = BrowserController(actions)
    
    planner = PlannerAgent(llm=llm)
    executor = ExecutorAgent(controller=controller)
    evaluator = EvaluatorAgent(llm=llm)
    
    orchestrator = Orchestrator(
        llm=llm,
        planner=planner,
        executor=executor,
        evaluator=evaluator,
    )
    
    # Execute task
    task = "Navigate to example.com and tell me what the main heading says"
    print(f"\n📋 Task: {task}")
    
    result = await orchestrator.execute_task(task)
    
    print(f"\n✅ Success: {result.success}")
    print(f"📊 Steps: {result.steps_executed}")
    if result.final_result:
        print(f"📄 Result: {result.final_result}")
    if result.error:
        print(f"❌ Error: {result.error}")
    
    # Execution log
    print("\n📜 Execution Log:")
    for entry in result.execution_log:
        phase = entry.get("phase", "unknown")
        print(f"   - {phase}")
    
    await browser.close()
    print("\n✨ Done!")


async def main():
    """Main entry point."""
    import sys
    
    if "--quick" in sys.argv:
        await run_single_task_demo()
    else:
        await run_orchestrator_demo()


if __name__ == "__main__":
    asyncio.run(main())

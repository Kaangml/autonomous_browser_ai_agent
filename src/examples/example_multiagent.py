"""Multi-Agent Browser Automation Example.

This example demonstrates the full multi-agent system:
1. Planner creates a multi-step plan using LLM
2. Executor runs each step
3. Results are collected and displayed

Requirements:
- Set GEMINI_API_KEY in .env (or another LLM provider)
- Run: uv run python -m src.examples.example_multiagent
"""

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
    print("🤖 Multi-Agent Browser Automation Example")
    print("=" * 50)
    
    # Initialize LLM provider
    try:
        llm = get_llm_provider()
        print(f"✅ LLM Provider: {type(llm).__name__}")
    except Exception as e:
        print(f"❌ Failed to initialize LLM: {e}")
        print("   Make sure you have set an API key in .env")
        return
    
    # Create agents
    planner = PlannerAgent(llm=llm)
    
    # Setup browser
    config = BrowserConfigManager.load_from_settings()
    browser = BrowserManager(config)
    await browser.start()
    
    actions = BrowserActions(browser)
    controller = BrowserController(actions)
    executor = ExecutorAgent(controller=controller)
    
    # Define the task
    task = "Go to example.com and extract the main heading and first paragraph"
    
    print(f"\n📋 Task: {task}")
    print("-" * 50)
    
    try:
        # Phase 1: Planning
        print("\n🔧 Phase 1: Planning...")
        steps = await planner.plan(task)
        
        print(f"   Generated {len(steps)} steps:")
        for i, step in enumerate(steps, 1):
            args_str = ", ".join(f"{k}={v}" for k, v in step.get("args", {}).items())
            print(f"   {i}. {step['type']}({args_str})")
        
        # Phase 2: Execution
        print("\n🚀 Phase 2: Executing...")
        page = None
        results = []
        
        for i, step in enumerate(steps, 1):
            result = await executor.execute(step, page)
            status = "✅" if result.get("ok") else "❌"
            print(f"   {status} Step {i}: {step['type']}")
            
            # Update page reference
            if result.get("page"):
                page = result["page"]
            
            # Collect results
            if result.get("ok") and result.get("result"):
                if result["result"] not in ("navigated", "clicked", "filled"):
                    results.append({
                        "step": i,
                        "type": step["type"],
                        "data": result["result"]
                    })
            
            # Stop on error
            if not result.get("ok"):
                print(f"      Error: {result.get('error')}")
                break
        
        # Phase 3: Results
        print("\n📄 Results:")
        print("-" * 50)
        
        if results:
            for r in results:
                data = str(r["data"])
                if len(data) > 200:
                    data = data[:200] + "..."
                print(f"Step {r['step']} ({r['type']}):")
                print(f"   {data}")
                print()
        else:
            print("   No data extracted")
        
        print("✅ Task completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await browser.close()
        print("\n🔒 Browser closed")


if __name__ == "__main__":
    asyncio.run(main())

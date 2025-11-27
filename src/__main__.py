#!/usr/bin/env python3
"""CLI entry point for autonomous browser agent.

Usage:
    uv run python -m src --url https://example.com --task "extract page title"
    uv run python -m src --help
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Optional


async def run_agent(url: str, task: str, headless: bool = True) -> dict:
    """Run the browser agent on a given URL with a task description.
    
    Returns a dict with the execution result.
    """
    from browser.browser_config import BrowserConfigManager, BrowserConfig
    from browser.browser import BrowserManager
    from browser.actions import BrowserActions
    from controller.browser_controller import BrowserController
    from agent.agent import Agent

    # Create browser config directly
    browser_config = BrowserConfig(
        headless=headless,
        viewport={"width": 1920, "height": 1080},
        timeout=30,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        stealth=True,
        channel=None,
        human_delay_min=0.1,
        human_delay_max=0.3,
    )
    config = BrowserConfigManager(browser_config)
    browser_manager = BrowserManager(config)
    actions = BrowserActions(browser_manager)
    controller = BrowserController(actions)

    # Setup agent with controller as tools
    agent = Agent(name="CLI-Agent")
    agent.tools = controller

    try:
        # Create the task with URL context
        full_task = f"Open {url} and {task}"
        agent.receive_task(full_task)

        # Plan and execute
        steps = await agent.plan_task(full_task)
        
        results = []
        current_page = None
        
        for step in steps:
            # Inject page from previous goto step if needed
            if step.get("type") in {"extract_text", "click", "fill", "links", "screenshot"}:
                if current_page and "page" not in step.get("args", {}):
                    step.setdefault("args", {})["page"] = current_page
            
            result = await agent.execute_step(step)
            agent.evaluate_result(result)
            results.append(result)
            
            # Track page from goto results
            if result.get("ok") and result.get("page"):
                current_page = result["page"]
            
            # Stop on first error
            if not result.get("ok"):
                break

        return {
            "ok": all(r.get("ok") for r in results),
            "task": full_task,
            "steps": steps,
            "results": results,
        }

    finally:
        await browser_manager.close()


def main():
    parser = argparse.ArgumentParser(
        prog="autonomous-browser-agent",
        description="Run an autonomous browser agent to perform web tasks",
    )
    parser.add_argument(
        "--url",
        "-u",
        required=True,
        help="Target URL to navigate to",
    )
    parser.add_argument(
        "--task",
        "-t",
        required=True,
        help='Task description (e.g., "extract the page title")',
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default: True)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with visible window",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )

    args = parser.parse_args()

    headless = not args.no_headless

    try:
        result = asyncio.run(run_agent(args.url, args.task, headless=headless))

        if args.json:
            # Filter out non-serializable page objects
            def clean_result(obj):
                if isinstance(obj, dict):
                    return {k: clean_result(v) for k, v in obj.items() if k != "page"}
                if isinstance(obj, list):
                    return [clean_result(i) for i in obj]
                if isinstance(obj, bytes):
                    return "<bytes>"
                return obj

            print(json.dumps(clean_result(result), indent=2, ensure_ascii=False))
        else:
            # Human-readable output
            print(f"\n{'='*60}")
            print(f"Task: {result['task']}")
            print(f"Status: {'✅ Success' if result['ok'] else '❌ Failed'}")
            print(f"{'='*60}")
            
            for i, (step, res) in enumerate(zip(result["steps"], result["results"]), 1):
                status = "✓" if res.get("ok") else "✗"
                step_type = step.get("type", "unknown")
                print(f"  {i}. [{status}] {step_type}: {step.get('args', {})}")
                if res.get("result") and step_type == "extract_text":
                    text = res["result"]
                    if len(text) > 200:
                        text = text[:200] + "..."
                    print(f"      → {text}")
                if res.get("error"):
                    print(f"      ⚠ Error: {res['error']}")
            
            print()

        sys.exit(0 if result["ok"] else 1)

    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

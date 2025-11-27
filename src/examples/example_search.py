#!/usr/bin/env python3
"""Example: Search DuckDuckGo and extract results.

Demonstrates:
- Navigation
- Form filling (search input)
- Waiting for results
- Extracting text

Run:
    uv run python -m src.examples.example_search
"""

from __future__ import annotations

import asyncio

from browser.browser_config import BrowserConfigManager, BrowserConfig
from browser.browser import BrowserManager
from browser.actions import BrowserActions
from controller.browser_controller import BrowserController


async def main():
    """Search DuckDuckGo for a term and extract first result titles."""
    
    search_query = "autonomous browser agent"
    
    browser_config = BrowserConfig(
        headless=True,
        viewport={"width": 1920, "height": 1080},
        timeout=30,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        stealth=True,
        human_delay_min=0.1,  # small delays for realism
        human_delay_max=0.3,
    )
    config = BrowserConfigManager(browser_config)

    browser = BrowserManager(config)
    actions = BrowserActions(browser)
    controller = BrowserController(actions)

    try:
        # 1. Go to DuckDuckGo
        print(f"Searching DuckDuckGo for: '{search_query}'...")
        result = await controller.execute_action({
            "type": "goto",
            "args": {"url": "https://duckduckgo.com"}
        })
        
        if not result["ok"]:
            print(f"Failed: {result.get('error')}")
            return
        
        page = result["page"]
        
        # 2. Fill the search box
        await controller.execute_action({
            "type": "fill",
            "args": {"page": page, "selector": 'input[name="q"]', "text": search_query}
        })
        
        # 3. Click search button (or submit form)
        await controller.execute_action({
            "type": "click",
            "args": {"page": page, "selector": 'button[type="submit"]'}
        })
        
        # 4. Wait for results to load
        await page.wait_for_selector('[data-testid="result"]', timeout=10000)
        
        # 5. Extract result titles
        titles = await page.eval_on_selector_all(
            '[data-testid="result-title-a"]',
            "nodes => nodes.map(n => n.innerText)"
        )
        
        print(f"\n✅ Found {len(titles)} results:\n")
        for i, title in enumerate(titles[:5], 1):
            print(f"  {i}. {title}")
        print()

    except Exception as e:
        print(f"Error during search: {e}")

    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

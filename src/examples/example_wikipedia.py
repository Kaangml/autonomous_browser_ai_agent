#!/usr/bin/env python3
"""Example: Scrape Wikipedia main page and extract featured article title.

This demonstrates a simple browser agent workflow:
1. Navigate to a URL
2. Extract text from a specific selector
3. Print the result

Run:
    uv run python -m src.examples.example_wikipedia
"""

from __future__ import annotations

import asyncio

from browser.browser_config import BrowserConfigManager, BrowserConfig
from browser.browser import BrowserManager
from browser.actions import BrowserActions
from controller.browser_controller import BrowserController


async def main():
    """Extract featured article title from Wikipedia main page."""
    
    # 1. Setup browser with config
    browser_config = BrowserConfig(
        headless=True,
        viewport={"width": 1920, "height": 1080},
        timeout=30,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        stealth=True,
    )
    config = BrowserConfigManager(browser_config)
    
    browser = BrowserManager(config)
    actions = BrowserActions(browser)
    controller = BrowserController(actions)

    try:
        # 2. Navigate to Wikipedia
        print("Navigating to Wikipedia...")
        goto_result = await controller.execute_action({
            "type": "goto",
            "args": {"url": "https://en.wikipedia.org/wiki/Main_Page"}
        })
        
        if not goto_result["ok"]:
            print(f"Failed to navigate: {goto_result.get('error')}")
            return
        
        page = goto_result["page"]
        
        # 3. Extract the featured article heading
        print("Extracting featured article...")
        extract_result = await controller.execute_action({
            "type": "extract_text",
            "args": {"page": page, "selector": "#mp-tfa b"}  # Featured article bold text
        })
        
        if extract_result["ok"]:
            print(f"\n✅ Today's Featured Article: {extract_result['result']}\n")
        else:
            # Fallback: extract page title
            title_result = await controller.execute_action({
                "type": "extract_text",
                "args": {"page": page, "selector": "title"}
            })
            if title_result["ok"]:
                print(f"\n✅ Page title: {title_result['result']}\n")
            else:
                print(f"Failed: {extract_result.get('error')}")
        
        # 4. Bonus: get some links
        print("Extracting links from main content...")
        links_result = await controller.execute_action({
            "type": "links",
            "args": {"page": page, "selector": "#mp-tfa"}
        })
        
        if links_result["ok"]:
            links = links_result["result"][:5]  # first 5 links
            print(f"Found {len(links_result['result'])} links. First 5:")
            for link in links:
                print(f"  - {link}")

    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

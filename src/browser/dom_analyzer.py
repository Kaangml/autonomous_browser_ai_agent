"""DOM Analyzer for extracting page structure and interactive elements.

This module provides intelligent DOM analysis for the planner agent,
allowing it to understand page structure and make informed decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from playwright.async_api import Page


@dataclass
class InteractiveElement:
    """Represents an interactive element on the page."""
    tag: str
    selector: str
    text: str
    element_type: str  # button, link, input, select, etc.
    attributes: Dict[str, str] = field(default_factory=dict)
    is_visible: bool = True
    bounding_box: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag": self.tag,
            "selector": self.selector,
            "text": self.text[:100] if self.text else "",  # Truncate long text
            "type": self.element_type,
            "visible": self.is_visible,
        }


@dataclass
class PageStructure:
    """Represents the analyzed structure of a page."""
    url: str
    title: str
    main_content_text: str
    interactive_elements: List[InteractiveElement]
    forms: List[Dict[str, Any]]
    navigation_links: List[Dict[str, str]]
    headings: List[Dict[str, str]]
    
    def to_prompt_context(self, max_elements: int = 20) -> str:
        """Convert page structure to a context string for LLM prompts."""
        lines = [
            f"## Current Page Analysis",
            f"URL: {self.url}",
            f"Title: {self.title}",
            "",
            "### Page Headings:",
        ]
        
        for h in self.headings[:10]:
            lines.append(f"  - [{h['level']}] {h['text']}")
        
        lines.extend([
            "",
            "### Interactive Elements (buttons, links, inputs):",
        ])
        
        for i, elem in enumerate(self.interactive_elements[:max_elements]):
            lines.append(f"  {i+1}. [{elem.element_type}] selector='{elem.selector}' text='{elem.text[:50]}'")
        
        if len(self.interactive_elements) > max_elements:
            lines.append(f"  ... and {len(self.interactive_elements) - max_elements} more elements")
        
        if self.forms:
            lines.extend([
                "",
                "### Forms on Page:",
            ])
            for form in self.forms[:5]:
                lines.append(f"  - Form: {form.get('action', 'no action')} with {len(form.get('fields', []))} fields")
        
        lines.extend([
            "",
            "### Main Content Preview:",
            self.main_content_text[:500] + "..." if len(self.main_content_text) > 500 else self.main_content_text,
        ])
        
        return "\n".join(lines)


class DOMAnalyzer:
    """Analyzes page DOM to extract structured information for planning."""
    
    def __init__(self, max_elements: int = 50):
        """Initialize analyzer.
        
        Args:
            max_elements: Maximum number of interactive elements to extract
        """
        self.max_elements = max_elements
    
    async def analyze(self, page: Page) -> PageStructure:
        """Analyze the current page and return structured information.
        
        Args:
            page: Playwright Page object
            
        Returns:
            PageStructure with all analyzed data
        """
        url = page.url
        title = await page.title()
        
        # Run analysis in parallel for performance
        interactive_elements = await self._extract_interactive_elements(page)
        forms = await self._extract_forms(page)
        navigation_links = await self._extract_navigation(page)
        headings = await self._extract_headings(page)
        main_content = await self._extract_main_content(page)
        
        return PageStructure(
            url=url,
            title=title,
            main_content_text=main_content,
            interactive_elements=interactive_elements,
            forms=forms,
            navigation_links=navigation_links,
            headings=headings,
        )
    
    async def _extract_interactive_elements(self, page: Page) -> List[InteractiveElement]:
        """Extract buttons, links, inputs, and other interactive elements."""
        elements = []
        
        # JavaScript to extract interactive elements
        js_code = """
        () => {
            const results = [];
            const selectors = [
                'button',
                'a[href]',
                'input:not([type="hidden"])',
                'select',
                'textarea',
                '[role="button"]',
                '[onclick]',
            ];
            
            const seen = new Set();
            
            for (const selector of selectors) {
                const nodes = document.querySelectorAll(selector);
                for (const node of nodes) {
                    // Skip hidden elements
                    const rect = node.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) continue;
                    
                    // Generate unique selector
                    let uniqueSelector = '';
                    if (node.id) {
                        uniqueSelector = '#' + node.id;
                    } else if (node.name) {
                        uniqueSelector = `${node.tagName.toLowerCase()}[name="${node.name}"]`;
                    } else if (node.className && typeof node.className === 'string') {
                        const classes = node.className.trim().split(/\\s+/).slice(0, 2).join('.');
                        if (classes) {
                            uniqueSelector = `${node.tagName.toLowerCase()}.${classes}`;
                        }
                    }
                    
                    if (!uniqueSelector) {
                        // Use nth-child as fallback
                        const parent = node.parentNode;
                        const index = Array.from(parent.children).indexOf(node) + 1;
                        uniqueSelector = `${node.tagName.toLowerCase()}:nth-child(${index})`;
                    }
                    
                    // Skip duplicates
                    if (seen.has(uniqueSelector)) continue;
                    seen.add(uniqueSelector);
                    
                    // Determine element type
                    let elementType = node.tagName.toLowerCase();
                    if (elementType === 'input') {
                        elementType = node.type || 'text';
                    } else if (elementType === 'a') {
                        elementType = 'link';
                    }
                    
                    results.push({
                        tag: node.tagName.toLowerCase(),
                        selector: uniqueSelector,
                        text: (node.innerText || node.value || node.placeholder || '').trim().substring(0, 100),
                        elementType: elementType,
                        attributes: {
                            type: node.type || '',
                            name: node.name || '',
                            href: node.href || '',
                            placeholder: node.placeholder || '',
                        },
                        boundingBox: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                        },
                    });
                    
                    if (results.length >= 50) break;
                }
                if (results.length >= 50) break;
            }
            
            return results;
        }
        """
        
        try:
            raw_elements = await page.evaluate(js_code)
            
            for raw in raw_elements[:self.max_elements]:
                elements.append(InteractiveElement(
                    tag=raw["tag"],
                    selector=raw["selector"],
                    text=raw["text"],
                    element_type=raw["elementType"],
                    attributes=raw["attributes"],
                    bounding_box=raw.get("boundingBox"),
                ))
        except Exception:
            pass  # Return empty list on error
        
        return elements
    
    async def _extract_forms(self, page: Page) -> List[Dict[str, Any]]:
        """Extract form structures from the page."""
        js_code = """
        () => {
            const forms = [];
            for (const form of document.querySelectorAll('form')) {
                const fields = [];
                for (const input of form.querySelectorAll('input, select, textarea')) {
                    if (input.type === 'hidden') continue;
                    fields.push({
                        name: input.name || '',
                        type: input.type || input.tagName.toLowerCase(),
                        required: input.required,
                        placeholder: input.placeholder || '',
                    });
                }
                forms.push({
                    action: form.action || '',
                    method: form.method || 'get',
                    fields: fields,
                });
            }
            return forms;
        }
        """
        
        try:
            return await page.evaluate(js_code)
        except Exception:
            return []
    
    async def _extract_navigation(self, page: Page) -> List[Dict[str, str]]:
        """Extract navigation links (nav, header, menu areas)."""
        js_code = """
        () => {
            const links = [];
            const navAreas = document.querySelectorAll('nav a, header a, [role="navigation"] a');
            for (const a of navAreas) {
                if (a.href && a.innerText.trim()) {
                    links.push({
                        text: a.innerText.trim().substring(0, 50),
                        href: a.href,
                    });
                }
                if (links.length >= 20) break;
            }
            return links;
        }
        """
        
        try:
            return await page.evaluate(js_code)
        except Exception:
            return []
    
    async def _extract_headings(self, page: Page) -> List[Dict[str, str]]:
        """Extract page headings for structure understanding."""
        js_code = """
        () => {
            const headings = [];
            for (const h of document.querySelectorAll('h1, h2, h3')) {
                const text = h.innerText.trim();
                if (text) {
                    headings.push({
                        level: h.tagName,
                        text: text.substring(0, 100),
                    });
                }
                if (headings.length >= 15) break;
            }
            return headings;
        }
        """
        
        try:
            return await page.evaluate(js_code)
        except Exception:
            return []
    
    async def _extract_main_content(self, page: Page) -> str:
        """Extract main page content text."""
        js_code = """
        () => {
            // Try to find main content area
            const main = document.querySelector('main, [role="main"], article, .content, #content');
            if (main) {
                return main.innerText.trim().substring(0, 2000);
            }
            // Fallback to body
            return document.body.innerText.trim().substring(0, 2000);
        }
        """
        
        try:
            return await page.evaluate(js_code)
        except Exception:
            return ""
    
    async def get_element_context(self, page: Page, selector: str) -> Dict[str, Any]:
        """Get detailed context about a specific element.
        
        Useful for the executor to understand element state before interaction.
        """
        js_code = f"""
        (selector) => {{
            const el = document.querySelector(selector);
            if (!el) return null;
            
            const rect = el.getBoundingClientRect();
            return {{
                exists: true,
                visible: rect.width > 0 && rect.height > 0,
                enabled: !el.disabled,
                text: el.innerText?.trim()?.substring(0, 100) || '',
                value: el.value || '',
                tagName: el.tagName.toLowerCase(),
                type: el.type || '',
                boundingBox: {{
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                }},
            }};
        }}
        """
        
        try:
            result = await page.evaluate(js_code, selector)
            return result or {"exists": False}
        except Exception:
            return {"exists": False, "error": "evaluation failed"}

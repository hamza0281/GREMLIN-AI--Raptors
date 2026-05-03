"""
Chaos-QA Page Crawler
Uses Playwright to discover and map all interactive elements on a target page.
Extracts forms, inputs, buttons, links — everything a chaos persona can attack.
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


@dataclass
class PageElement:
    """Represents a single interactive element on the page."""
    selector: str
    tag: str  # input, button, a, select, textarea
    element_type: str  # text, email, password, submit, etc.
    name: str  # field name or label
    placeholder: str
    label: str  # associated <label> text
    is_required: bool
    is_visible: bool
    current_value: str
    options: List[str] = field(default_factory=list)  # for select elements

    def get_field_type(self) -> str:
        """Return a human-readable field type for the model prompt."""
        if self.element_type in ("text", ""):
            # Try to infer from name/placeholder
            name_lower = (self.name + self.placeholder + self.label).lower()
            if "email" in name_lower:
                return "email"
            if "phone" in name_lower or "tel" in name_lower:
                return "phone number"
            if "password" in name_lower or "pass" in name_lower:
                return "password"
            if "url" in name_lower or "website" in name_lower:
                return "URL"
            if "date" in name_lower:
                return "date"
            if "name" in name_lower:
                return "name"
            return "text"
        return self.element_type

    def get_display_name(self) -> str:
        """Best human-readable name for this element."""
        return self.label or self.placeholder or self.name or f"{self.tag}[{self.element_type}]"


@dataclass
class PageMap:
    """Complete map of all interactive elements on a page."""
    url: str
    title: str
    input_fields: List[PageElement] = field(default_factory=list)
    buttons: List[PageElement] = field(default_factory=list)
    links: List[PageElement] = field(default_factory=list)
    forms: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def total_elements(self) -> int:
        return len(self.input_fields) + len(self.buttons) + len(self.links)

    def summary(self) -> str:
        return (
            f"Page: {self.title} ({self.url})\n"
            f"  Input fields: {len(self.input_fields)}\n"
            f"  Buttons: {len(self.buttons)}\n"
            f"  Links: {len(self.links)}\n"
            f"  Forms: {len(self.forms)}"
        )


class PageCrawler:
    """Crawls a target website and extracts all interactive elements."""

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self, headless: bool = True):
        """Launch browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=headless)
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) ChaosQA/1.0",
        )
        self.page = await self._context.new_page()

    async def close(self):
        """Close browser."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def crawl_page(self, url: str) -> PageMap:
        """Navigate to URL and extract all interactive elements."""
        if not self.page:
            await self.start()

        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await self.page.wait_for_timeout(1500)  # Let JS render
        except Exception as e:
            print(f"[Crawler] Navigation error: {e}")
            return PageMap(url=url, title="Error loading page")

        title = await self.page.title()
        page_map = PageMap(url=url, title=title)

        # Extract input fields
        page_map.input_fields = await self._extract_inputs()

        # Extract buttons
        page_map.buttons = await self._extract_buttons()

        # Extract links
        page_map.links = await self._extract_links()

        # Extract form structure
        page_map.forms = await self._extract_forms()

        return page_map

    async def _extract_inputs(self) -> List[PageElement]:
        """Extract all input fields, textareas, and selects."""
        elements = []
        selectors = [
            "input:not([type='hidden']):not([type='submit']):not([type='button']):not([type='image'])",
            "textarea",
            "select",
        ]
        for selector in selectors:
            items = await self.page.query_selector_all(selector)
            for i, item in enumerate(items):
                try:
                    tag = await item.evaluate("el => el.tagName.toLowerCase()")
                    el_type = await item.get_attribute("type") or ""
                    name = await item.get_attribute("name") or ""
                    placeholder = await item.get_attribute("placeholder") or ""
                    required = await item.get_attribute("required") is not None
                    is_visible = await item.is_visible()
                    current_val = await item.input_value() if tag != "select" else ""

                    # Get label text
                    el_id = await item.get_attribute("id") or ""
                    label = ""
                    if el_id:
                        label_el = await self.page.query_selector(f'label[for="{el_id}"]')
                        if label_el:
                            label = (await label_el.inner_text()).strip()

                    # If no label, try aria-label
                    if not label:
                        label = await item.get_attribute("aria-label") or ""

                    # Build unique selector
                    unique_selector = await self._build_selector(item, tag, el_type, name, el_id, i)

                    # Get options for select
                    options = []
                    if tag == "select":
                        option_els = await item.query_selector_all("option")
                        for opt in option_els:
                            opt_text = await opt.inner_text()
                            options.append(opt_text.strip())

                    if is_visible:
                        elements.append(PageElement(
                            selector=unique_selector,
                            tag=tag,
                            element_type=el_type,
                            name=name,
                            placeholder=placeholder,
                            label=label,
                            is_required=required,
                            is_visible=is_visible,
                            current_value=current_val,
                            options=options,
                        ))
                except Exception:
                    continue
        return elements

    async def _extract_buttons(self) -> List[PageElement]:
        """Extract all buttons and submit inputs."""
        elements = []
        button_items = await self.page.query_selector_all(
            "button, input[type='submit'], input[type='button'], [role='button']"
        )
        for i, item in enumerate(button_items):
            try:
                tag = await item.evaluate("el => el.tagName.toLowerCase()")
                text = ""
                if tag == "input":
                    text = await item.get_attribute("value") or ""
                else:
                    text = (await item.inner_text()).strip()
                is_visible = await item.is_visible()
                el_id = await item.get_attribute("id") or ""
                btn_type = await item.get_attribute("type") or "button"

                unique_selector = await self._build_selector(item, tag, btn_type, text, el_id, i)

                if is_visible and text:
                    elements.append(PageElement(
                        selector=unique_selector,
                        tag=tag,
                        element_type=btn_type,
                        name=text,
                        placeholder="",
                        label=text,
                        is_required=False,
                        is_visible=is_visible,
                        current_value="",
                    ))
            except Exception:
                continue
        return elements

    async def _extract_links(self) -> List[PageElement]:
        """Extract navigation links."""
        elements = []
        link_items = await self.page.query_selector_all("a[href]")
        for i, item in enumerate(link_items[:20]):  # Limit to 20 links
            try:
                href = await item.get_attribute("href") or ""
                text = (await item.inner_text()).strip()
                is_visible = await item.is_visible()

                if is_visible and text and not href.startswith(("javascript:", "#", "mailto:")):
                    elements.append(PageElement(
                        selector=f"a:has-text('{text[:30]}')" if text else f"a[href='{href}']",
                        tag="a",
                        element_type="link",
                        name=text[:50],
                        placeholder="",
                        label=text[:50],
                        is_required=False,
                        is_visible=is_visible,
                        current_value=href,
                    ))
            except Exception:
                continue
        return elements

    async def _extract_forms(self) -> List[Dict[str, Any]]:
        """Extract form structure (action, method)."""
        forms = []
        form_els = await self.page.query_selector_all("form")
        for form in form_els:
            try:
                action = await form.get_attribute("action") or ""
                method = await form.get_attribute("method") or "GET"
                form_id = await form.get_attribute("id") or ""
                field_count = await form.evaluate(
                    "el => el.querySelectorAll('input, textarea, select').length"
                )
                forms.append({
                    "action": action,
                    "method": method.upper(),
                    "id": form_id,
                    "field_count": field_count,
                })
            except Exception:
                continue
        return forms

    async def _build_selector(self, item, tag, el_type, name, el_id, index) -> str:
        """Build a reliable CSS selector for an element."""
        if el_id:
            return f"#{el_id}"
        if name and tag == "input":
            return f'{tag}[name="{name}"]'
        if name and tag == "textarea":
            return f'{tag}[name="{name}"]'
        if el_type and tag == "input":
            return f'{tag}[type="{el_type}"]:nth-of-type({index + 1})'
        return f"{tag}:nth-of-type({index + 1})"

    async def take_screenshot(self, path: str = None) -> bytes:
        """Capture current page screenshot."""
        if self.page:
            return await self.page.screenshot(path=path, full_page=False)
        return b""

    async def discover_all_pages(self, base_url: str, max_pages: int = 10) -> List[str]:
        """Discover linked pages from the base URL (simple breadth-first)."""
        visited = set()
        to_visit = [base_url]
        discovered = []

        while to_visit and len(discovered) < max_pages:
            url = to_visit.pop(0)
            if url in visited:
                continue
            visited.add(url)
            discovered.append(url)

            try:
                page_map = await self.crawl_page(url)
                for link in page_map.links:
                    href = link.current_value
                    if href and href.startswith(("http", "/")):
                        if href.startswith("/"):
                            # Relative URL — join with base
                            from urllib.parse import urljoin
                            href = urljoin(base_url, href)
                        if base_url.split("/")[2] in href and href not in visited:
                            to_visit.append(href)
            except Exception:
                continue

        return discovered


# Quick test
if __name__ == "__main__":
    async def test():
        crawler = PageCrawler()
        await crawler.start(headless=True)
        page_map = await crawler.crawl_page("https://www.google.com")
        print(page_map.summary())
        for inp in page_map.input_fields:
            print(f"  Field: {inp.get_display_name()} (type={inp.get_field_type()}, selector={inp.selector})")
        for btn in page_map.buttons:
            print(f"  Button: {btn.name} (selector={btn.selector})")
        await crawler.close()

    asyncio.run(test())

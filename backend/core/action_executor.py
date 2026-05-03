"""
Chaos-QA Action Executor
Executes chaos actions via Playwright — fills forms with garbage,
clicks buttons randomly, submits forms, simulates different interaction styles.
"""

import asyncio
import random
from typing import Optional, Dict, Any
from playwright.async_api import Page
from .crawler import PageElement


class ActionResult:
    """Result of executing a chaos action."""
    def __init__(self):
        self.success: bool = False
        self.action_type: str = ""
        self.element_name: str = ""
        self.input_value: str = ""
        self.error_message: str = ""
        self.screenshot_before: Optional[bytes] = None
        self.screenshot_after: Optional[bytes] = None
        self.console_errors: list = []
        self.network_errors: list = []
        self.dialog_appeared: bool = False
        self.dialog_message: str = ""
        self.page_crashed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "action_type": self.action_type,
            "element_name": self.element_name,
            "input_value": self.input_value[:200],  # Truncate for display
            "error_message": self.error_message,
            "console_errors": self.console_errors,
            "network_errors": self.network_errors,
            "dialog_appeared": self.dialog_appeared,
            "dialog_message": self.dialog_message,
            "page_crashed": self.page_crashed,
        }


class ActionExecutor:
    """Executes chaos actions on the browser page."""

    def __init__(self, page: Page):
        self.page = page
        self._console_errors: list = []
        self._network_errors: list = []
        self._dialog_message: str = ""
        self._dialog_appeared: bool = False
        self._setup_done = False

    async def setup_monitors(self):
        """Set up console and network error monitors."""
        if self._setup_done:
            return
        self._setup_done = True

        # Monitor console errors
        self.page.on("console", self._on_console)

        # Monitor page errors (uncaught exceptions)
        self.page.on("pageerror", self._on_page_error)

        # Monitor dialogs (alerts, confirms, prompts — often sign of XSS)
        self.page.on("dialog", self._on_dialog)

        # Monitor failed requests
        self.page.on("requestfailed", self._on_request_failed)

    def _on_console(self, msg):
        if msg.type in ("error", "warning"):
            self._console_errors.append({
                "type": msg.type,
                "text": msg.text[:300],
            })

    def _on_page_error(self, error):
        self._console_errors.append({
            "type": "exception",
            "text": str(error)[:300],
        })

    async def _on_dialog(self, dialog):
        self._dialog_appeared = True
        self._dialog_message = dialog.message[:200]
        await dialog.dismiss()

    def _on_request_failed(self, request):
        self._network_errors.append({
            "url": request.url[:200],
            "method": request.method,
            "failure": request.failure or "unknown",
        })

    def _clear_errors(self):
        """Clear error buffers before each action."""
        self._console_errors = []
        self._network_errors = []
        self._dialog_appeared = False
        self._dialog_message = ""

    async def fill_field(self, element: PageElement, chaos_input: str) -> ActionResult:
        """Fill an input field with chaos text."""
        result = ActionResult()
        result.action_type = "fill"
        result.element_name = element.get_display_name()
        result.input_value = chaos_input
        self._clear_errors()

        try:
            await self.setup_monitors()

            # Screenshot before
            result.screenshot_before = await self.page.screenshot()

            # Clear existing value first
            el = await self.page.query_selector(element.selector)
            if not el:
                # Try alternative selectors
                el = await self._find_element_fallback(element)

            if not el:
                result.error_message = f"Element not found: {element.selector}"
                return result

            # Clear and type
            await el.click()
            await el.fill("")
            await el.type(chaos_input, delay=10)  # Type character by character

            # Small wait to let JS validators fire
            await self.page.wait_for_timeout(300)

            # Screenshot after
            result.screenshot_after = await self.page.screenshot()
            result.success = True

        except Exception as e:
            result.error_message = str(e)[:300]
            result.page_crashed = "Target closed" in str(e) or "crashed" in str(e).lower()
            try:
                result.screenshot_after = await self.page.screenshot()
            except Exception:
                pass

        # Collect errors
        result.console_errors = self._console_errors.copy()
        result.network_errors = self._network_errors.copy()
        result.dialog_appeared = self._dialog_appeared
        result.dialog_message = self._dialog_message

        return result

    async def click_button(self, element: PageElement) -> ActionResult:
        """Click a button element."""
        result = ActionResult()
        result.action_type = "click"
        result.element_name = element.get_display_name()
        self._clear_errors()

        try:
            await self.setup_monitors()
            result.screenshot_before = await self.page.screenshot()

            el = await self.page.query_selector(element.selector)
            if not el:
                el = await self._find_element_fallback(element)

            if not el:
                result.error_message = f"Button not found: {element.selector}"
                return result

            await el.click(timeout=5000)
            await self.page.wait_for_timeout(500)

            result.screenshot_after = await self.page.screenshot()
            result.success = True

        except Exception as e:
            result.error_message = str(e)[:300]
            result.page_crashed = "Target closed" in str(e)
            try:
                result.screenshot_after = await self.page.screenshot()
            except Exception:
                pass

        result.console_errors = self._console_errors.copy()
        result.network_errors = self._network_errors.copy()
        result.dialog_appeared = self._dialog_appeared
        result.dialog_message = self._dialog_message

        return result

    async def submit_form(self, element: PageElement) -> ActionResult:
        """Submit a form by pressing Enter or clicking submit button."""
        result = ActionResult()
        result.action_type = "submit"
        result.element_name = element.get_display_name()
        self._clear_errors()

        try:
            await self.setup_monitors()
            result.screenshot_before = await self.page.screenshot()

            el = await self.page.query_selector(element.selector)
            if el:
                await el.press("Enter")
            else:
                # Try clicking a submit button
                submit = await self.page.query_selector(
                    "button[type='submit'], input[type='submit'], button:has-text('Submit')"
                )
                if submit:
                    await submit.click()

            await self.page.wait_for_timeout(1000)
            result.screenshot_after = await self.page.screenshot()
            result.success = True

        except Exception as e:
            result.error_message = str(e)[:300]
            result.page_crashed = "Target closed" in str(e)
            try:
                result.screenshot_after = await self.page.screenshot()
            except Exception:
                pass

        result.console_errors = self._console_errors.copy()
        result.network_errors = self._network_errors.copy()
        result.dialog_appeared = self._dialog_appeared
        result.dialog_message = self._dialog_message

        return result

    async def rapid_fire_click(self, element: PageElement, clicks: int = 5) -> ActionResult:
        """Rapidly click an element multiple times (Speed Demon persona)."""
        result = ActionResult()
        result.action_type = "rapid_click"
        result.element_name = element.get_display_name()
        result.input_value = f"{clicks} rapid clicks"
        self._clear_errors()

        try:
            await self.setup_monitors()
            result.screenshot_before = await self.page.screenshot()

            el = await self.page.query_selector(element.selector)
            if el:
                for _ in range(clicks):
                    await el.click(delay=30)
                    await self.page.wait_for_timeout(50)

            await self.page.wait_for_timeout(500)
            result.screenshot_after = await self.page.screenshot()
            result.success = True

        except Exception as e:
            result.error_message = str(e)[:300]
            result.page_crashed = "Target closed" in str(e)

        result.console_errors = self._console_errors.copy()
        result.network_errors = self._network_errors.copy()
        result.dialog_appeared = self._dialog_appeared
        result.dialog_message = self._dialog_message

        return result

    async def _find_element_fallback(self, element: PageElement):
        """Try alternative selectors if primary one fails."""
        fallback_selectors = []
        if element.name:
            fallback_selectors.append(f'[name="{element.name}"]')
            fallback_selectors.append(f'[placeholder*="{element.name}"]')
            fallback_selectors.append(f'[aria-label*="{element.name}"]')
        if element.label:
            fallback_selectors.append(f'[aria-label="{element.label}"]')

        for sel in fallback_selectors:
            try:
                el = await self.page.query_selector(sel)
                if el and await el.is_visible():
                    return el
            except Exception:
                continue
        return None

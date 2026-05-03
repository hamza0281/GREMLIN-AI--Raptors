"""
GremlinAI Engine — The Main Orchestrator
Coordinates the full multi-step pipeline:
  1. Crawl target page → discover elements
  2. Select persona → generate chaos input
  3. Execute action via Playwright
  4. Detect errors → classify bugs
  5. Generate report → calculate score

This is the brain that turns a dumb model into a smart QA tool.
"""

import asyncio
import time
import uuid
import random
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field

from .model_client import ChaosModelClient
from .crawler import PageCrawler, PageMap, PageElement
from .personas import PERSONAS, PersonaType, ChaosPersona, ALL_PERSONA_TYPES
from .action_executor import ActionExecutor, ActionResult
from .error_detector import ErrorDetector, DetectedBug
from .bug_reporter import BugReporter
from .chaos_scorer import ChaosScorer, ChaosScore


@dataclass
class ScanConfig:
    """Configuration for a chaos scan."""
    url: str
    personas: List[PersonaType] = field(default_factory=lambda: list(ALL_PERSONA_TYPES))
    max_actions_per_element: int = 2  # How many personas attack each element
    max_pages: int = 1  # How many pages to scan (1 = just the given URL)
    headless: bool = True
    output_dir: str = "./reports"


@dataclass
class ScanEvent:
    """An event emitted during scanning for real-time updates."""
    event_type: str  # "action", "bug", "progress", "score", "info", "error"
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {"type": self.event_type, "data": self.data}


class ChaosEngine:
    """The main chaos testing engine."""

    def __init__(self, model_name: str = "qwen2.5:0.5b"):
        self.model_client = ChaosModelClient(model_name=model_name)
        self.crawler = PageCrawler()
        self.error_detector = ErrorDetector()
        self.bug_reporter = BugReporter()
        self.chaos_scorer = ChaosScorer()
        self._event_callback: Optional[Callable] = None
        self._bugs: List[DetectedBug] = []
        self._total_actions = 0
        self._scan_id = ""

    def on_event(self, callback: Callable):
        """Register a callback for real-time scan events."""
        self._event_callback = callback

    async def _emit(self, event_type: str, data: Dict[str, Any] = None):
        """Emit an event to the callback."""
        event = ScanEvent(event_type=event_type, data=data or {})
        if self._event_callback:
            if asyncio.iscoroutinefunction(self._event_callback):
                await self._event_callback(event)
            else:
                self._event_callback(event)

    async def run_scan(self, config: ScanConfig) -> Dict[str, Any]:
        """Run a complete chaos scan. Returns the full report."""
        self._scan_id = str(uuid.uuid4())[:8]
        self._bugs = []
        self._total_actions = 0
        start_time = time.time()

        await self._emit("info", {"message": f"🚀 GremlinAI scan starting: {config.url}", "scan_id": self._scan_id})

        # Step 1: Check model health
        await self._emit("info", {"message": "🔍 Checking model connection..."})
        model_ok = await self.model_client.check_health()
        if not model_ok:
            await self._emit("error", {"message": "❌ Ollama model not available. Is Ollama running?"})
            return {"error": "Model not available"}

        await self._emit("info", {"message": f"✅ Model ready: {self.model_client.model_name}"})

        # Step 2: Start browser
        await self._emit("info", {"message": "🌐 Launching browser..."})
        try:
            await self.crawler.start(headless=config.headless)
        except Exception as e:
            await self._emit("error", {"message": f"❌ Browser launch failed: {e}"})
            return {"error": str(e)}

        # Step 3: Discover pages
        pages_to_scan = [config.url]
        if config.max_pages > 1:
            await self._emit("info", {"message": f"🔗 Discovering linked pages (max {config.max_pages})..."})
            pages_to_scan = await self.crawler.discover_all_pages(config.url, config.max_pages)
            await self._emit("info", {"message": f"📄 Found {len(pages_to_scan)} pages to scan"})

        # Step 4: Scan each page
        for page_idx, page_url in enumerate(pages_to_scan):
            await self._emit("progress", {
                "message": f"📄 Scanning page {page_idx + 1}/{len(pages_to_scan)}: {page_url}",
                "current_page": page_idx + 1,
                "total_pages": len(pages_to_scan),
            })

            # Crawl the page
            page_map = await self.crawler.crawl_page(page_url)
            await self._emit("info", {
                "message": f"  Found: {len(page_map.input_fields)} inputs, {len(page_map.buttons)} buttons, {len(page_map.links)} links"
            })

            if page_map.total_elements == 0:
                await self._emit("info", {"message": "  ⚠️ No interactive elements found, skipping"})
                continue

            # Create action executor for this page
            executor = ActionExecutor(self.crawler.page)

            # Step 5: Attack each input field with chaos personas
            await self._attack_inputs(
                page_map, executor, config.personas,
                config.max_actions_per_element, page_url
            )

            # Step 6: Try clicking buttons after chaos inputs
            await self._attack_buttons(page_map, executor, page_url)

        # Step 7: Calculate score
        duration = time.time() - start_time
        score = self.chaos_scorer.calculate(self._total_actions, self._bugs)

        await self._emit("score", {
            "score": score.to_dict(),
            "duration": round(duration, 1),
        })

        # Step 8: Generate report
        scan_info = {
            "scan_id": self._scan_id,
            "url": config.url,
            "duration": duration,
            "total_actions": self._total_actions,
            "pages_scanned": len(pages_to_scan),
            "model": self.model_client.model_name,
        }

        self.bug_reporter.output_dir = config.output_dir
        report = self.bug_reporter.generate_report(self._bugs, scan_info)
        report["chaos_score"] = score.to_dict()

        # Save reports
        json_path = self.bug_reporter.save_json_report(report)
        md_report = self.bug_reporter.generate_markdown_report(self._bugs, scan_info)
        md_path = self.bug_reporter.save_markdown_report(md_report)
        self.bug_reporter.save_screenshots(self._bugs)

        await self._emit("info", {
            "message": f"📋 Reports saved: {json_path}, {md_path}"
        })

        # Cleanup
        await self.crawler.close()
        await self.model_client.close()

        await self._emit("info", {
            "message": (
                f"\n🏁 Scan complete!\n"
                f"   Total actions: {self._total_actions}\n"
                f"   Bugs found: {len(self._bugs)}\n"
                f"   Chaos Score: {score.score:.0f}/100 ({score.grade})\n"
                f"   {score.verdict}"
            )
        })

        return report

    async def _attack_inputs(
        self, page_map: PageMap, executor: ActionExecutor,
        persona_types: List[PersonaType], max_per_element: int, page_url: str
    ):
        """Attack all input fields with chaos personas."""
        for element in page_map.input_fields:
            # Pick random personas for this element
            selected_personas = random.sample(
                persona_types, min(max_per_element, len(persona_types))
            )

            for persona_type in selected_personas:
                persona = PERSONAS[persona_type]

                await self._emit("action", {
                    "persona": persona.name,
                    "persona_icon": persona.icon,
                    "element": element.get_display_name(),
                    "field_type": element.get_field_type(),
                    "action": "generating_input",
                })

                # Generate chaos input
                chaos_input = await self.model_client.generate_chaos_input(
                    field_name=element.get_display_name(),
                    field_type=element.get_field_type(),
                    persona_prompt=persona.prompt_template,
                )

                await self._emit("action", {
                    "persona": persona.name,
                    "persona_icon": persona.icon,
                    "element": element.get_display_name(),
                    "action": "filling",
                    "input": chaos_input[:100],
                })

                # Execute the action
                result = await executor.fill_field(element, chaos_input)
                self._total_actions += 1

                # Detect bugs
                bug = self.error_detector.analyze(
                    result, persona.name, persona.icon, page_url
                )

                if bug:
                    bug.screenshot_before = result.screenshot_before
                    bug.screenshot_after = result.screenshot_after
                    self._bugs.append(bug)
                    await self._emit("bug", {
                        "bug": bug.to_dict(),
                        "message": f"🐛 Bug found! [{bug.severity.value.upper()}] {bug.title}",
                    })
                else:
                    await self._emit("action", {
                        "persona": persona.name,
                        "persona_icon": persona.icon,
                        "element": element.get_display_name(),
                        "action": "survived",
                        "input": chaos_input[:60],
                    })

                # Small delay between actions
                await asyncio.sleep(0.3)

    async def _attack_buttons(
        self, page_map: PageMap, executor: ActionExecutor, page_url: str
    ):
        """Click buttons after chaos data has been filled in."""
        speed_demon = PERSONAS[PersonaType.SPEED_DEMON]
        for button in page_map.buttons:
            await self._emit("action", {
                "persona": speed_demon.name,
                "persona_icon": speed_demon.icon,
                "element": button.get_display_name(),
                "action": "clicking",
            })

            result = await executor.click_button(button)
            self._total_actions += 1

            bug = self.error_detector.analyze(
                result, speed_demon.name, speed_demon.icon, page_url
            )
            if bug:
                self._bugs.append(bug)
                await self._emit("bug", {
                    "bug": bug.to_dict(),
                    "message": f"🐛 Bug found! [{bug.severity.value.upper()}] {bug.title}",
                })

            await asyncio.sleep(0.3)


# ═══════════════════════════════════════════════════════════════
# CLI ENTRY POINT — run a scan from command line
# ═══════════════════════════════════════════════════════════════

async def run_cli_scan(url: str, personas: List[str] = None, headless: bool = True):
    """Run a chaos scan from the command line."""

    # Parse persona types
    persona_types = ALL_PERSONA_TYPES
    if personas:
        persona_types = [PersonaType(p) for p in personas if p in PersonaType.__members__.values()]

    config = ScanConfig(
        url=url,
        personas=persona_types,
        max_actions_per_element=2,
        max_pages=1,
        headless=headless,
    )

    engine = ChaosEngine()

    # Print events to console
    def print_event(event: ScanEvent):
        msg = event.data.get("message", "")
        if msg:
            print(msg)
        elif event.event_type == "action":
            d = event.data
            print(f"  {d.get('persona_icon', '🤖')} {d.get('persona', 'Bot')} → {d.get('action', '?')} '{d.get('element', '')}' {d.get('input', '')[:50]}")

    engine.on_event(print_event)
    report = await engine.run_scan(config)
    return report


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.google.com"
    print(f"\n{'='*60}")
    print(f"  GREMLIN-AI — Autonomous Chaos Testing")
    print(f"  Target: {url}")
    print(f"{'='*60}\n")
    asyncio.run(run_cli_scan(url))

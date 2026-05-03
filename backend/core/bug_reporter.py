"""
GremlinAI Bug Reporter
Generates structured bug reports in JSON and Markdown format.
"""

import json
import os
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
from .error_detector import DetectedBug, BugSeverity


class BugReporter:
    """Generates professional bug reports from detected bugs."""

    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(self, bugs: List[DetectedBug], scan_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a complete scan report with all bugs."""
        report = {
            "scan_id": scan_info.get("scan_id", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "target_url": scan_info.get("url", ""),
            "duration_seconds": scan_info.get("duration", 0),
            "total_actions": scan_info.get("total_actions", 0),
            "pages_scanned": scan_info.get("pages_scanned", 0),
            "model_used": scan_info.get("model", "qwen2.5:0.5b"),
            "summary": {
                "total_bugs": len(bugs),
                "critical": len([b for b in bugs if b.severity == BugSeverity.CRITICAL]),
                "high": len([b for b in bugs if b.severity == BugSeverity.HIGH]),
                "medium": len([b for b in bugs if b.severity == BugSeverity.MEDIUM]),
                "low": len([b for b in bugs if b.severity == BugSeverity.LOW]),
            },
            "bugs": [b.to_dict() for b in bugs],
        }
        return report

    def save_json_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save report as JSON file."""
        if not filename:
            filename = f"gremlin_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return path

    def generate_markdown_report(self, bugs: List[DetectedBug], scan_info: Dict[str, Any]) -> str:
        """Generate a Markdown-formatted bug report."""
        lines = []
        lines.append("# 👾 GremlinAI Scan Report\n")
        lines.append(f"**Target:** {scan_info.get('url', 'N/A')}")
        lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Model:** {scan_info.get('model', 'qwen2.5:0.5b')}")
        lines.append(f"**Duration:** {scan_info.get('duration', 0):.1f}s")
        lines.append(f"**Actions Performed:** {scan_info.get('total_actions', 0)}")
        lines.append("")

        # Summary
        critical = len([b for b in bugs if b.severity == BugSeverity.CRITICAL])
        high = len([b for b in bugs if b.severity == BugSeverity.HIGH])
        medium = len([b for b in bugs if b.severity == BugSeverity.MEDIUM])
        low = len([b for b in bugs if b.severity == BugSeverity.LOW])

        lines.append("## 📊 Summary\n")
        lines.append(f"| Severity | Count |")
        lines.append(f"|----------|-------|")
        lines.append(f"| 🔴 Critical | {critical} |")
        lines.append(f"| 🟠 High | {high} |")
        lines.append(f"| 🟡 Medium | {medium} |")
        lines.append(f"| 🟢 Low | {low} |")
        lines.append(f"| **Total** | **{len(bugs)}** |")
        lines.append("")

        # Individual bugs
        if bugs:
            lines.append("## 🐛 Bug Details\n")
            for bug in bugs:
                severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                icon = severity_icon.get(bug.severity.value, "⚪")
                lines.append(f"### {icon} [{bug.bug_id}] {bug.title}\n")
                lines.append(f"- **Severity:** {bug.severity.value.upper()}")
                lines.append(f"- **Category:** {bug.category.value}")
                lines.append(f"- **Found by:** {bug.persona_icon} {bug.persona_name}")
                lines.append(f"- **Element:** `{bug.element_name}`")
                lines.append(f"- **Chaos Input:** `{bug.chaos_input[:100]}`")
                lines.append(f"- **URL:** {bug.url}")
                lines.append("")
                lines.append(f"**Description:** {bug.description}")
                lines.append("")
                if bug.reproduction_steps:
                    lines.append("**Steps to Reproduce:**")
                    for step in bug.reproduction_steps:
                        lines.append(f"  {step}")
                    lines.append("")
                if bug.console_errors:
                    lines.append("**Console Errors:**")
                    lines.append("```")
                    for err in bug.console_errors[:3]:
                        lines.append(f"  [{err.get('type', 'error')}] {err.get('text', '')[:150]}")
                    lines.append("```")
                    lines.append("")
                lines.append("---\n")
        else:
            lines.append("## ✅ No bugs detected!\n")
            lines.append("Your app survived the chaos. Nice work! 💪\n")

        return "\n".join(lines)

    def save_markdown_report(self, report_md: str, filename: str = None) -> str:
        """Save markdown report to file."""
        if not filename:
            filename = f"gremlin_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(report_md)
        return path

    def save_screenshots(self, bugs: List[DetectedBug]) -> None:
        """Save bug screenshots to files."""
        ss_dir = os.path.join(self.output_dir, "screenshots")
        os.makedirs(ss_dir, exist_ok=True)
        for bug in bugs:
            if bug.screenshot_before:
                path = os.path.join(ss_dir, f"{bug.bug_id}_before.png")
                with open(path, "wb") as f:
                    f.write(bug.screenshot_before)
            if bug.screenshot_after:
                path = os.path.join(ss_dir, f"{bug.bug_id}_after.png")
                with open(path, "wb") as f:
                    f.write(bug.screenshot_after)

"""
Chaos-QA Error Detector
Analyzes action results to detect and classify bugs.
Uses heuristics (NOT the LLM) for reliable severity classification.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import re


class BugSeverity(str, Enum):
    CRITICAL = "critical"  # App crashes, security vulnerabilities
    HIGH = "high"          # Major functionality broken
    MEDIUM = "medium"      # Errors that don't crash but are bad
    LOW = "low"            # Minor issues, warnings


class BugCategory(str, Enum):
    SECURITY = "security"          # XSS, SQL injection, etc.
    CRASH = "crash"                # App crashes or becomes unresponsive
    VALIDATION = "validation"      # Missing input validation
    ERROR_HANDLING = "error_handling"  # Unhandled exceptions
    UX = "ux"                      # Poor user experience
    NETWORK = "network"            # API/network failures
    RENDERING = "rendering"        # Visual/display issues


@dataclass
class DetectedBug:
    """A bug found during chaos testing."""
    bug_id: str
    severity: BugSeverity
    category: BugCategory
    title: str
    description: str
    persona_name: str
    persona_icon: str
    element_name: str
    chaos_input: str
    action_type: str
    console_errors: List[Dict]
    network_errors: List[Dict]
    screenshot_before: Optional[bytes] = None
    screenshot_after: Optional[bytes] = None
    url: str = ""
    reproduction_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bug_id": self.bug_id,
            "severity": self.severity.value,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "persona_name": self.persona_name,
            "persona_icon": self.persona_icon,
            "element_name": self.element_name,
            "chaos_input": self.chaos_input[:200],
            "action_type": self.action_type,
            "console_errors": self.console_errors[:5],
            "network_errors": self.network_errors[:5],
            "url": self.url,
            "reproduction_steps": self.reproduction_steps,
        }


# ═══════════════════════════════════════════════════════════════
# DETECTION PATTERNS — heuristic-based, no LLM needed
# ═══════════════════════════════════════════════════════════════

SECURITY_PATTERNS = [
    (r"<script.*?>", "Potential XSS — script tag accepted"),
    (r"alert\s*\(", "XSS alert triggered"),
    (r"onerror\s*=", "Event handler injection accepted"),
    (r"javascript:", "JavaScript URI accepted"),
    (r"SELECT.*FROM|DROP\s+TABLE|INSERT\s+INTO|DELETE\s+FROM", "SQL keywords accepted without sanitization"),
    (r"\.\./\.\./", "Path traversal pattern accepted"),
]

CRASH_PATTERNS = [
    (r"target closed", "Page/tab crashed"),
    (r"navigation.*failed", "Navigation failure — page may have crashed"),
    (r"execution context was destroyed", "JavaScript context destroyed"),
    (r"net::ERR_", "Network error causing crash"),
]

ERROR_PATTERNS = [
    (r"uncaught.*error", "Unhandled JavaScript error"),
    (r"unhandled.*rejection", "Unhandled Promise rejection"),
    (r"typeerror", "TypeError — likely null/undefined access"),
    (r"referenceerror", "ReferenceError — undefined variable"),
    (r"syntaxerror", "SyntaxError in application code"),
    (r"rangeerror", "RangeError — value out of bounds"),
]


class ErrorDetector:
    """Detects and classifies bugs from action results."""

    def __init__(self):
        self._bug_counter = 0

    def analyze(
        self,
        action_result,  # ActionResult from action_executor
        persona_name: str,
        persona_icon: str,
        page_url: str,
    ) -> Optional[DetectedBug]:
        """Analyze an action result and return a DetectedBug if issues found."""

        issues = []

        # Check 1: Dialog appeared (often XSS indicator)
        if action_result.dialog_appeared:
            issues.append({
                "severity": BugSeverity.CRITICAL,
                "category": BugCategory.SECURITY,
                "title": f"Alert dialog triggered by chaos input in '{action_result.element_name}'",
                "description": (
                    f"An alert/confirm dialog appeared with message: '{action_result.dialog_message}'. "
                    f"This may indicate an XSS vulnerability. The chaos input was: '{action_result.input_value[:100]}'"
                ),
            })

        # Check 2: Page crashed
        if action_result.page_crashed:
            issues.append({
                "severity": BugSeverity.CRITICAL,
                "category": BugCategory.CRASH,
                "title": f"Page crashed when interacting with '{action_result.element_name}'",
                "description": (
                    f"The page crashed or became unresponsive after {action_result.action_type} action. "
                    f"Error: {action_result.error_message}"
                ),
            })

        # Check 3: Console errors
        for error in action_result.console_errors:
            error_text = error.get("text", "").lower()
            error_type = error.get("type", "")

            if error_type == "exception":
                severity = BugSeverity.HIGH
                category = BugCategory.ERROR_HANDLING

                # Check if it's a security-related error
                for pattern, desc in SECURITY_PATTERNS:
                    if re.search(pattern, action_result.input_value, re.IGNORECASE):
                        if "alert" in error_text or "script" in error_text:
                            severity = BugSeverity.CRITICAL
                            category = BugCategory.SECURITY
                            break

                issues.append({
                    "severity": severity,
                    "category": category,
                    "title": f"Unhandled exception in '{action_result.element_name}'",
                    "description": f"Exception: {error.get('text', 'Unknown')[:200]}",
                })

            elif error_type == "error":
                # Check if it matches known patterns
                matched = False
                for pattern, desc in ERROR_PATTERNS:
                    if re.search(pattern, error_text):
                        issues.append({
                            "severity": BugSeverity.MEDIUM,
                            "category": BugCategory.ERROR_HANDLING,
                            "title": f"{desc} in '{action_result.element_name}'",
                            "description": f"Console error: {error.get('text', '')[:200]}",
                        })
                        matched = True
                        break

                if not matched and "error" in error_text:
                    issues.append({
                        "severity": BugSeverity.LOW,
                        "category": BugCategory.ERROR_HANDLING,
                        "title": f"Console error when interacting with '{action_result.element_name}'",
                        "description": f"Error: {error.get('text', '')[:200]}",
                    })

        # Check 4: Network errors (5xx = server error from our chaos input)
        for net_err in action_result.network_errors:
            failure = str(net_err.get("failure", ""))
            issues.append({
                "severity": BugSeverity.HIGH if "500" in failure else BugSeverity.MEDIUM,
                "category": BugCategory.NETWORK,
                "title": f"Network request failed after chaos input in '{action_result.element_name}'",
                "description": f"Request to {net_err.get('url', 'unknown')[:100]} failed: {failure}",
            })

        # Check 5: Security pattern analysis on the input itself
        if action_result.success and action_result.input_value:
            for pattern, desc in SECURITY_PATTERNS:
                if re.search(pattern, action_result.input_value, re.IGNORECASE):
                    # The chaotic input contained a security payload — if no error,
                    # that might mean the app accepted it without sanitization
                    if not action_result.console_errors and not action_result.error_message:
                        issues.append({
                            "severity": BugSeverity.MEDIUM,
                            "category": BugCategory.VALIDATION,
                            "title": f"Potential {desc} — input accepted without validation in '{action_result.element_name}'",
                            "description": (
                                f"The input '{action_result.input_value[:80]}' was accepted without any "
                                f"visible error or validation. This may indicate missing input sanitization."
                            ),
                        })
                    break  # One security check per action is enough

        # Check 6: Missing input validation
        # If a typed field (email, number, url) accepted garbage without any complaint, flag it
        if action_result.success and action_result.input_value and not issues:
            field_name_lower = action_result.element_name.lower()
            input_val = action_result.input_value

            # Email field accepted non-email
            if "email" in field_name_lower and "@" not in input_val and len(input_val) > 2:
                issues.append({
                    "severity": BugSeverity.LOW,
                    "category": BugCategory.VALIDATION,
                    "title": f"Email field '{action_result.element_name}' accepted non-email input",
                    "description": (
                        f"The email field accepted '{input_val[:80]}' which is not a valid email. "
                        f"Consider adding email format validation."
                    ),
                })

            # Number/age field accepted text
            if any(w in field_name_lower for w in ["age", "number", "phone", "amount", "price", "quantity"]):
                if input_val and not input_val.replace(".", "").replace("-", "").replace("+", "").isdigit():
                    issues.append({
                        "severity": BugSeverity.LOW,
                        "category": BugCategory.VALIDATION,
                        "title": f"Numeric field '{action_result.element_name}' accepted non-numeric input",
                        "description": (
                            f"The numeric field accepted '{input_val[:80]}' which is not a number. "
                            f"Consider adding numeric validation."
                        ),
                    })

            # URL field accepted non-URL
            if any(w in field_name_lower for w in ["url", "website", "link"]):
                if input_val and not input_val.startswith(("http://", "https://", "ftp://")):
                    issues.append({
                        "severity": BugSeverity.LOW,
                        "category": BugCategory.VALIDATION,
                        "title": f"URL field '{action_result.element_name}' accepted non-URL input",
                        "description": (
                            f"The URL field accepted '{input_val[:80]}' which is not a valid URL. "
                            f"Consider adding URL format validation."
                        ),
                    })

        if not issues:
            return None

        # Return the highest severity issue
        issues.sort(key=lambda x: list(BugSeverity).index(x["severity"]))
        top_issue = issues[0]

        self._bug_counter += 1
        bug_id = f"CHAOS-{self._bug_counter:04d}"

        # Build reproduction steps
        steps = [
            f"1. Navigate to {page_url}",
            f"2. Find the '{action_result.element_name}' element",
            f"3. {action_result.action_type.title()} with input: `{action_result.input_value[:100]}`",
            f"4. Observe: {top_issue['title']}",
        ]

        return DetectedBug(
            bug_id=bug_id,
            severity=top_issue["severity"],
            category=top_issue["category"],
            title=top_issue["title"],
            description=top_issue["description"],
            persona_name=persona_name,
            persona_icon=persona_icon,
            element_name=action_result.element_name,
            chaos_input=action_result.input_value,
            action_type=action_result.action_type,
            console_errors=action_result.console_errors,
            network_errors=action_result.network_errors,
            screenshot_before=action_result.screenshot_before,
            screenshot_after=action_result.screenshot_after,
            url=page_url,
            reproduction_steps=steps,
        )

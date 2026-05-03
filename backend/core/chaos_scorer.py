"""
Chaos-QA Chaos Scorer
Calculates a "Chaos Resilience Score" — how well a website
handles chaotic, unexpected user behavior.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from .error_detector import DetectedBug, BugSeverity


@dataclass
class ChaosScore:
    """The chaos resilience score for a tested website."""
    total_actions: int
    survived: int
    bugs_found: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    score: float  # 0-100
    grade: str  # A+, A, B+, B, C, D, F
    verdict: str  # Human-readable summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_actions": self.total_actions,
            "survived": self.survived,
            "bugs_found": self.bugs_found,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "score": round(self.score, 1),
            "grade": self.grade,
            "verdict": self.verdict,
        }


# Severity penalty weights
SEVERITY_WEIGHTS = {
    BugSeverity.CRITICAL: 15,  # -15 points per critical bug
    BugSeverity.HIGH: 8,       # -8 per high
    BugSeverity.MEDIUM: 4,     # -4 per medium
    BugSeverity.LOW: 1,        # -1 per low
}

GRADES = [
    (95, "A+", "Your app is chaos-proof. Impressive! 🏆"),
    (85, "A", "Excellent resilience. Minor edges to smooth. 💪"),
    (75, "B+", "Good job, but some gaps need attention. 👍"),
    (65, "B", "Decent, but chaos found real weaknesses. ⚠️"),
    (50, "C", "Significant issues. Chaos testing revealed problems. 🔧"),
    (35, "D", "Major vulnerabilities. Your app needs hardening. 🚨"),
    (0, "F", "Your app did not survive the chaos. Critical fixes needed. 💀"),
]


class ChaosScorer:
    """Calculates chaos resilience scores."""

    def calculate(self, total_actions: int, bugs: List[DetectedBug]) -> ChaosScore:
        """Calculate the chaos resilience score."""
        if total_actions == 0:
            return ChaosScore(
                total_actions=0, survived=0, bugs_found=0,
                critical_count=0, high_count=0, medium_count=0, low_count=0,
                score=100, grade="N/A", verdict="No actions performed",
            )

        critical = len([b for b in bugs if b.severity == BugSeverity.CRITICAL])
        high = len([b for b in bugs if b.severity == BugSeverity.HIGH])
        medium = len([b for b in bugs if b.severity == BugSeverity.MEDIUM])
        low = len([b for b in bugs if b.severity == BugSeverity.LOW])

        # Calculate penalty
        penalty = (
            critical * SEVERITY_WEIGHTS[BugSeverity.CRITICAL]
            + high * SEVERITY_WEIGHTS[BugSeverity.HIGH]
            + medium * SEVERITY_WEIGHTS[BugSeverity.MEDIUM]
            + low * SEVERITY_WEIGHTS[BugSeverity.LOW]
        )

        # Base score starts at 100, deduct penalties
        # Scale penalty relative to total actions
        max_penalty = total_actions * 2  # Normalize
        scaled_penalty = min(penalty, max_penalty) / max_penalty * 100

        score = max(0, 100 - scaled_penalty)

        # Automatic cap: if any critical bugs, score can't exceed 60
        if critical > 0:
            score = min(score, 60)

        # Determine grade
        grade = "F"
        verdict = ""
        for threshold, g, v in GRADES:
            if score >= threshold:
                grade = g
                verdict = v
                break

        survived = total_actions - len(bugs)

        return ChaosScore(
            total_actions=total_actions,
            survived=survived,
            bugs_found=len(bugs),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            score=score,
            grade=grade,
            verdict=verdict,
        )

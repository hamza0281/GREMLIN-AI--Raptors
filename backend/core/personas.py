"""
Chaos-QA Persona System
6 specialized AI chaos personas, each exploiting the tiny model's weaknesses 
differently to target specific categories of bugs.

Each persona has a unique prompt template that guides the model to generate
specific types of chaotic input — but the model's own hallucinations make
each run unpredictable and creative.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List


class PersonaType(str, Enum):
    CONFUSED_GRANDMA = "confused_grandma"
    ACCIDENTAL_HACKER = "accidental_hacker"
    SPEED_DEMON = "speed_demon"
    TODDLER = "toddler"
    OVERTHINKING_DEV = "overthinking_dev"
    INTERNATIONAL_TRAVELER = "international_traveler"


@dataclass
class ChaosPersona:
    """A chaos testing persona with specialized prompts."""
    name: str
    persona_type: PersonaType
    icon: str
    description: str
    target_bugs: List[str]
    temperature: float  # Higher = more chaotic
    prompt_template: str
    action_style: str  # How this persona interacts with the page

    def get_prompt(self, field_name: str, field_type: str) -> str:
        """Generate the prompt for this persona targeting a specific field."""
        return self.prompt_template.format(
            field_name=field_name, field_type=field_type
        )


# ═══════════════════════════════════════════════════════════════
# THE 6 CHAOS PERSONAS
# ═══════════════════════════════════════════════════════════════

PERSONA_CONFUSED_GRANDMA = ChaosPersona(
    name="The Confused Grandma",
    persona_type=PersonaType.CONFUSED_GRANDMA,
    icon="👵",
    description="Puts phone numbers in email fields, writes stories in name fields, confuses every input type",
    target_bugs=["Input validation", "Type mismatch handling", "Error message UX", "Form usability"],
    temperature=1.5,
    prompt_template=(
        'You are an elderly grandmother who is confused by computers. '
        'You see a form field labeled "{field_name}" which expects {field_type}. '
        'You don\'t understand what it wants. Type something wrong — maybe your '
        'phone number, a recipe, your cat\'s name, or a story. '
        'Reply with ONLY what you type in the field, nothing else:'
    ),
    action_style="slow_and_confused",
)

PERSONA_ACCIDENTAL_HACKER = ChaosPersona(
    name="The Accidental Hacker",
    persona_type=PersonaType.ACCIDENTAL_HACKER,
    icon="🏴‍☠️",
    description="Naturally generates SQL injection, XSS, code snippets — the model has seen these in training data",
    target_bugs=["XSS vulnerabilities", "SQL injection", "Command injection", "HTML injection", "Security holes"],
    temperature=1.3,
    prompt_template=(
        'Complete this security test payload for a "{field_name}" field ({field_type}). '
        'Pick ONE and modify it creatively:\n'
        '- <script>alert(document.cookie)</script>\n'
        '- \' OR 1=1; DROP TABLE users;--\n'
        '- {{{{constructor.constructor("return this")()}}}}\n'
        '- ../../../etc/passwd\n'
        '- <img src=x onerror=alert(1)>\n'
        'Reply with ONLY your modified payload:'
    ),
    action_style="technical_and_precise",
)

PERSONA_SPEED_DEMON = ChaosPersona(
    name="The Speed Demon",
    persona_type=PersonaType.SPEED_DEMON,
    icon="⚡",
    description="Submits forms instantly, double-clicks, rapid-fires — tests race conditions",
    target_bugs=["Race conditions", "Double-submit bugs", "Loading state failures", "Debounce issues"],
    temperature=1.2,
    prompt_template=(
        'You are in a huge rush. Quickly type the SHORTEST possible thing for '
        'the "{field_name}" field ({field_type}). Maybe just one character, '
        'or nothing, or a single number. Be as brief as possible. '
        'Reply with ONLY what you type:'
    ),
    action_style="rapid_fire",
)

PERSONA_TODDLER = ChaosPersona(
    name="The Toddler",
    persona_type=PersonaType.TODDLER,
    icon="🧒",
    description="Keyboard smashing, random characters, pure gibberish — stress testing at its finest",
    target_bugs=["Unhandled exceptions", "Crash on unexpected input", "Null handling", "Encoding errors"],
    temperature=2.0,  # Maximum chaos
    prompt_template=(
        'Smash the keyboard randomly for the "{field_name}" field. Example: '
        'a;sldkfj;as8df7@#$%^&*()_+{{}}|:\"<>?/.,mn and 🔥💀👻🎭\n'
        'Now YOU smash the keyboard. Reply with ONLY random characters:'
    ),
    action_style="random_smashing",
)

PERSONA_OVERTHINKING_DEV = ChaosPersona(
    name="The Overthinking Dev",
    persona_type=PersonaType.OVERTHINKING_DEV,
    icon="🤓",
    description="Pastes JSON, markdown, code blocks, extremely long strings — edge case finder",
    target_bugs=["Buffer overflow", "Rendering bugs", "Markdown injection", "Data truncation", "Max length"],
    temperature=1.4,
    prompt_template=(
        'You are a developer who overthinks everything. For the "{field_name}" '
        'field ({field_type}), you decide to paste something complex — maybe a JSON '
        'object, a Python function, a markdown table, a very long string, or a '
        'configuration file. Reply with ONLY what you paste:'
    ),
    action_style="deliberate_and_complex",
)

PERSONA_INTERNATIONAL_TRAVELER = ChaosPersona(
    name="The International Traveler",
    persona_type=PersonaType.INTERNATIONAL_TRAVELER,
    icon="🌍",
    description="Types in random languages, emojis, RTL text, special Unicode — i18n chaos",
    target_bugs=["Encoding issues", "RTL layout breaks", "Emoji rendering", "Unicode edge cases", "i18n bugs"],
    temperature=1.6,
    prompt_template=(
        'You are a traveler who speaks many languages. For the "{field_name}" '
        'field ({field_type}), type in a mix of languages — Arabic, Chinese, Hindi, '
        'Japanese, Korean, Russian, emojis, and special Unicode characters. '
        'Mix them all together. Reply with ONLY the text:'
    ),
    action_style="multilingual_chaos",
)

# All personas in a dict for easy access
PERSONAS = {
    PersonaType.CONFUSED_GRANDMA: PERSONA_CONFUSED_GRANDMA,
    PersonaType.ACCIDENTAL_HACKER: PERSONA_ACCIDENTAL_HACKER,
    PersonaType.SPEED_DEMON: PERSONA_SPEED_DEMON,
    PersonaType.TODDLER: PERSONA_TODDLER,
    PersonaType.OVERTHINKING_DEV: PERSONA_OVERTHINKING_DEV,
    PersonaType.INTERNATIONAL_TRAVELER: PERSONA_INTERNATIONAL_TRAVELER,
}

ALL_PERSONA_TYPES = list(PersonaType)


def get_persona(persona_type: PersonaType) -> ChaosPersona:
    """Get a persona by type."""
    return PERSONAS[persona_type]


def get_all_personas() -> list:
    """Get all personas as a list of dicts for API response."""
    return [
        {
            "type": p.persona_type.value,
            "name": p.name,
            "icon": p.icon,
            "description": p.description,
            "target_bugs": p.target_bugs,
        }
        for p in PERSONAS.values()
    ]

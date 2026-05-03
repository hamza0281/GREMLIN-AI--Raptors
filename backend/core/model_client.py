"""
Chaos-QA Model Client
Wrapper around Ollama for generating chaotic inputs using a tiny LLM.
The model's hallucinations ARE the feature — we weaponize its inability
to follow instructions into creative, unpredictable test inputs.
"""

import httpx
import json
import re
import random
import asyncio
from typing import Optional


# Fallback chaos inputs when model fails completely
FALLBACK_CHAOS = {
    "text": [
        "'; DROP TABLE users;--",
        "<script>alert('XSS')</script>",
        "Robert'); DROP TABLE Students;--",
        "a" * 500,
        "",
        "   ",
        "null",
        "undefined",
        "NaN",
        "true",
        "-1",
        "0",
        "99999999999999999",
        "🔥💀👻🎭",
        "${7*7}",
        "{{constructor.constructor('return this')()}}",
        "../../../etc/passwd",
        "<img src=x onerror=alert(1)>",
        "%00%0d%0a",
        "<!--",
    ],
    "email": [
        "notanemail",
        "a@",
        "@gmail.com",
        "test@test@test.com",
        "'; DROP TABLE users;--@evil.com",
        "<script>alert(1)</script>@xss.com",
        "a" * 200 + "@test.com",
        "",
        "test@.com",
        "test@com.",
    ],
    "number": [
        "abc",
        "-99999999",
        "0.0000001",
        "Infinity",
        "NaN",
        "1e999",
        "",
        "12.34.56",
        "--1",
        "9" * 50,
    ],
    "password": [
        "",
        "a",
        "a" * 1000,
        "password",
        "' OR '1'='1",
        "<script>alert(document.cookie)</script>",
        "パスワード",
        "🔑🔒",
    ],
    "url": [
        "not-a-url",
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "ftp://evil.com/malware.exe",
        "",
        "//evil.com",
        "http://localhost:22",
    ],
}


class ChaosModelClient:
    """Interface to Ollama for generating chaotic test inputs."""

    def __init__(self, model_name: str = "qwen2.5:0.5b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.timeout = 30.0  # seconds per generation
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def check_health(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.base_url}/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                available = [m["name"] for m in models]
                # Check if our model (or a variant) is available
                for name in available:
                    if self.model_name.split(":")[0] in name:
                        return True
                print(f"[ModelClient] Model {self.model_name} not found. Available: {available}")
                return False
            return False
        except Exception as e:
            print(f"[ModelClient] Ollama health check failed: {e}")
            return False

    async def generate_raw(self, prompt: str, temperature: float = 1.5) -> str:
        """Send a prompt to the model and get raw text back.
        High temperature = more chaos = better for us!
        """
        client = await self._get_client()
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.95,
                "num_predict": 150,  # Keep outputs short
                "repeat_penalty": 1.0,  # Don't penalize repetition — chaos is good
            },
        }
        try:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
            else:
                print(f"[ModelClient] Ollama returned {resp.status_code}")
                return ""
        except httpx.TimeoutException:
            print("[ModelClient] Ollama request timed out")
            return ""
        except Exception as e:
            print(f"[ModelClient] Generation error: {e}")
            return ""

    async def generate_chaos_input(
        self, field_name: str, field_type: str, persona_prompt: str
    ) -> str:
        """Generate a chaotic input for a specific form field using a persona prompt.
        
        This is the core function. The persona prompt tells the model what
        kind of chaos to generate, and the model's natural hallucinations
        make it even more unpredictable.
        
        Returns the chaotic input string, with fallback if model fails.
        """
        # Build the full prompt
        full_prompt = persona_prompt.format(
            field_name=field_name, field_type=field_type
        )

        # Try generation with high temperature for maximum chaos
        raw = await self.generate_raw(full_prompt, temperature=1.5)

        # Attempt to extract just the input value
        parsed = self._extract_input(raw)

        if parsed and len(parsed) > 0:
            return parsed

        # Retry with simpler prompt (validation layer)
        simple_prompt = f'Type something unexpected for a "{field_name}" field:'
        raw_retry = await self.generate_raw(simple_prompt, temperature=2.0)
        parsed_retry = self._extract_input(raw_retry)

        if parsed_retry and len(parsed_retry) > 0:
            return parsed_retry

        # Final fallback: use pre-built chaos inputs
        return self._get_fallback(field_type)

    def _extract_input(self, raw_text: str) -> str:
        """Extract the actual input value from model's verbose output.
        The model often wraps the answer in explanations — we strip those.
        """
        if not raw_text:
            return ""

        # If model returned JSON, try to extract value
        json_match = re.search(r'"(?:value|input|text|answer)"\s*:\s*"([^"]*)"', raw_text)
        if json_match:
            return json_match.group(1)

        # If output is short and clean (< 200 chars), use as-is
        # This is often the case with tiny models
        lines = raw_text.strip().split("\n")
        if len(lines) == 1 and len(lines[0]) < 200:
            # Remove common prefixes the model adds
            cleaned = re.sub(
                r"^(Here'?s?|I'?d? ?type|The input:?|Answer:?|Output:?|Result:?|Value:?)\s*:?\s*",
                "",
                lines[0],
                flags=re.IGNORECASE,
            )
            # Remove surrounding quotes
            cleaned = cleaned.strip("\"'`")
            return cleaned if cleaned else raw_text.strip()

        # Multi-line output: take the first non-empty, non-explanation line
        for line in lines:
            line = line.strip()
            if line and not any(
                line.lower().startswith(p) for p in ["here", "i ", "the ", "this ", "note", "sure"]
            ):
                return line.strip("\"'`")

        # Last resort: return first line
        return lines[0].strip("\"'`") if lines else ""

    def _get_fallback(self, field_type: str) -> str:
        """Get a random pre-built chaos input as fallback."""
        category = "text"
        field_lower = field_type.lower()
        if "email" in field_lower or "mail" in field_lower:
            category = "email"
        elif "number" in field_lower or "tel" in field_lower or "phone" in field_lower:
            category = "number"
        elif "password" in field_lower or "pass" in field_lower:
            category = "password"
        elif "url" in field_lower or "link" in field_lower or "website" in field_lower:
            category = "url"

        return random.choice(FALLBACK_CHAOS.get(category, FALLBACK_CHAOS["text"]))

    async def generate_action_suggestion(self, page_description: str) -> str:
        """Ask the model what a chaotic user might do on a page.
        The model's confused suggestions become our test actions!
        """
        prompt = (
            f"You are a confused, distracted user on a website. "
            f"The page has these elements: {page_description}\n"
            f"What would you click or do next? Reply with ONLY the action, like "
            f"'click the Submit button' or 'scroll down'. One action only."
        )
        raw = await self.generate_raw(prompt, temperature=1.8)
        return self._extract_input(raw) or "click a random button"


# Quick test
if __name__ == "__main__":
    async def test():
        client = ChaosModelClient()
        print("Health check:", await client.check_health())

        # Test chaos generation
        result = await client.generate_chaos_input(
            "Email Address", "email",
            'You are filling a web form. Type something in the "{field_name}" field. Reply with ONLY what you type:'
        )
        print(f"Chaos input for email: {repr(result)}")

        result2 = await client.generate_chaos_input(
            "Password", "password",
            'Type something unexpected in the "{field_name}" field. Reply with ONLY the text:'
        )
        print(f"Chaos input for password: {repr(result2)}")
        await client.close()

    asyncio.run(test())

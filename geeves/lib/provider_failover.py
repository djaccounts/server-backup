"""
provider_failover.py — Priority-ordered API provider stack with automatic failover.

Provider stack (ranked by preference):
  1. OpenRouter (owl-alpha)        — primary, best quality/cost
  2. Groq (llama-3.3-70b)          — fast fallback
  3. NVIDIA (llama-3.1-70b)        — secondary cloud
  4. Ollama local (qwen2.5:7b)     — offline last resort, no key needed

Usage:
    from lib.provider_failover import ProviderStack

    stack = ProviderStack()
    response = stack.chat("Summarise yesterday's Airtable changes")

    # Or with explicit provider override:
    response = stack.chat("Hello", provider="groq")

    # Check which provider was actually used:
    print(stack.last_provider)   # e.g. "groq"
    print(stack.last_model)      # e.g. "llama-3.3-70b-versatile"

Environment variables expected (from /root/.hermes/.env):
    OPENROUTER_API_KEY, GROQ_API_KEY, NVIDIA_API_KEY
    OLLAMA_BASE_URL (default: http://localhost:11434/v1)
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Ordered list: first = highest priority.  Each entry maps to env var, base URL,
# and the model string that provider expects.
PROVIDER_STACK: list[dict[str, Any]] = [
    {
        "name": "openrouter",
        "env_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openrouter/owl-alpha",
        "models": ["openrouter/owl-alpha"],
        "timeout": 60,
    },
    {
        "name": "groq",
        "env_key": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ],
        "timeout": 30,
    },
    {
        "name": "nvidia",
        "env_key": "NVIDIA_API_KEY",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "meta/llama-3.1-70b-instruct",
        "models": [
            "meta/llama-3.1-70b-instruct",
            "meta/llama-3.1-8b-instruct",
        ],
        "timeout": 45,
    },
    {
        "name": "ollama",
        "env_key": None,            # no key needed for local
        "base_url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        "model": "qwen2.5:7b",
        "models": ["qwen2.5:7b", "llama3.1:8b", "mistral:7b"],
        "timeout": 120,
    },
]

# Path to Hermes .env so we can load keys without depending on shell dotenv
HERMES_ENV_PATH = Path("/root/.hermes/.env")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_hermes_env() -> dict[str, str]:
    """Parse /root/.hermes/.env into a dict (skips comments and blanks)."""
    env: dict[str, str] = {}
    if not HERMES_ENV_PATH.exists():
        return env
    for line in HERMES_ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _chat_completion(
    api_key: str,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    timeout: int = 60,
) -> dict[str, Any]:
    """
    Call a chat/completions endpoint compatible with the OpenAI format.
    Returns the parsed JSON response.
    Raises on HTTP error or timeout.
    """
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    # OpenRouter-specific headers (safe to send to others — they ignore them)
    if "openrouter" in base_url:
        headers["HTTP-Referer"] = "https://geeves.local"
        headers["X-Title"] = "Geeves"

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(
            f"HTTP {e.code} from {url}: {body[:500]}"
        ) from e


# ---------------------------------------------------------------------------
# ProviderStack
# ---------------------------------------------------------------------------

@dataclass
class ProviderStack:
    """
    Try each provider in priority order until one succeeds.

    Attributes:
        providers:       Ordered list of provider config dicts.
        last_provider:   Name of the provider that succeeded (or None).
        last_model:      Model string that was actually used.
        last_response:   Full JSON response body from the winning provider.
        errors:          {provider_name: error_message} for every attempt.
    """

    providers: list[dict[str, Any]] = field(default_factory=lambda: list(PROVIDER_STACK))
    last_provider: Optional[str] = None
    last_model: Optional[str] = None
    last_response: Optional[dict[str, Any]] = None
    errors: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._hermes_env = _load_hermes_env()

    # ---- public API -------------------------------------------------------

    def chat(
        self,
        user_message: str,
        system_message: str = "You are a helpful assistant.",
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """
        Send a chat message through the provider stack.

        Args:
            user_message:   The user prompt.
            system_message: System prompt prepended to the conversation.
            provider:       If set, skip the stack and use only this provider.
            model:          Override the model for the chosen provider.

        Returns:
            The assistant's reply text.

        Raises:
            RuntimeError if every provider in the stack fails.
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

        providers = self.providers
        if provider:
            providers = [p for p in providers if p["name"] == provider]
            if not providers:
                raise ValueError(
                    f"Provider '{provider}' not in stack. "
                    f"Available: {[p['name'] for p in self.providers]}"
                )

        self.errors = {}
        self.last_provider = None
        self.last_model = None
        self.last_response = None

        for p in providers:
            name = p["name"]
            api_key = self._resolve_key(p)
            if not api_key:
                msg = f"No API key for provider '{name}' (env var: {p.get('env_key')})"
                logger.warning(msg)
                self.errors[name] = msg
                continue

            # Try each model variant for this provider
            models = [model] if model else p.get("models", [p["model"]])
            for m in models:
                try:
                    logger.info("Trying provider=%s model=%s", name, m)
                    resp = _chat_completion(
                        api_key=api_key,
                        base_url=p["base_url"],
                        model=m,
                        messages=messages,
                        timeout=p.get("timeout", 60),
                    )
                    reply = resp["choices"][0]["message"]["content"]
                    self.last_provider = name
                    self.last_model = m
                    self.last_response = resp
                    logger.info("Success: provider=%s model=%s", name, m)
                    return reply
                except Exception as exc:
                    err = f"{type(exc).__name__}: {exc}"
                    logger.warning("Failed provider=%s model=%s → %s", name, m, err)
                    self.errors[f"{name}/{m}"] = err
                    continue

        # All providers exhausted
        detail = "; ".join(f"{k}: {v}" for k, v in self.errors.items())
        raise RuntimeError(f"All providers failed. Errors: {detail}")

    def chat_json(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Like .chat() but returns the full JSON response dict."""
        self.chat(*args, **kwargs)
        return self.last_response  # type: ignore[return-value]

    def status(self) -> dict[str, Any]:
        """Return a snapshot of the stack's current state."""
        return {
            "providers": [p["name"] for p in self.providers],
            "last_provider": self.last_provider,
            "last_model": self.last_model,
            "errors": self.errors,
        }

    # ---- internals --------------------------------------------------------

    def _resolve_key(self, provider_cfg: dict[str, Any]) -> Optional[str]:
        env_var = provider_cfg.get("env_key")
        if not env_var:
            return ""  # Ollama — no key needed
        # Check runtime env first, then parsed .env file
        return os.environ.get(env_var) or self._hermes_env.get(env_var)


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

def quick_chat(message: str, **kwargs: Any) -> str:
    """One-liner: create a stack, send a message, return the reply."""
    return ProviderStack().chat(message, **kwargs)


# ---------------------------------------------------------------------------
# CLI (for quick testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    prompt = " ".join(sys.argv[1:]) or "Reply with exactly: OK"
    stack = ProviderStack()

    print(f"Prompt: {prompt}")
    print(f"Stack:  {[p['name'] for p in stack.providers]}")
    print("—" * 40)

    try:
        reply = stack.chat(prompt)
        print(f"\n✅ Provider: {stack.last_provider}")
        print(f"   Model:    {stack.last_model}")
        print(f"   Reply:    {reply}")
    except RuntimeError as exc:
        print(f"\n❌ {exc}")
        sys.exit(1)

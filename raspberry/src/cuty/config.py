"""Centralized environment configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigurationError(ValueError):
    pass


_EXAMPLE_KEYS = {
    "your_key_here",
    "your_real_key",
    "your_api_key_here",
    "sk-your-real-key",
    "sk-your-api-key",
}


@dataclass(frozen=True)
class Config:
    api_key: str
    provider: str = "gemini"
    input_device: str | None = None
    output_device: str | None = None
    log_level: str = "INFO"
    debug: bool = False
    model: str = "gemini-3.8-live"

    @classmethod
    def from_env(cls) -> Config:
        provider = os.getenv("CUTY_AI_PROVIDER", "gemini").strip().lower()
        if provider not in {"gemini", "openai"}:
            raise ConfigurationError("CUTY_AI_PROVIDER must be gemini or openai.")
        key_name = "GEMINI_API_KEY" if provider == "gemini" else "OPENAI_API_KEY"
        key = os.getenv(key_name, "").strip()
        if not key:
            raise ConfigurationError(f"{key_name} is missing. Set it in your environment or .env file.")
        if key.casefold() in _EXAMPLE_KEYS:
            raise ConfigurationError(f"{key_name} is an example placeholder. Set a real API key.")
        level = os.getenv("CUTY_LOG_LEVEL", "INFO").upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
            raise ConfigurationError("CUTY_LOG_LEVEL must be DEBUG, INFO, WARNING, or ERROR.")
        return cls(
            api_key=key,
            provider=provider,
            input_device=os.getenv("CUTY_AUDIO_INPUT_DEVICE") or None,
            output_device=os.getenv("CUTY_AUDIO_OUTPUT_DEVICE") or None,
            log_level=level,
            debug=os.getenv("CUTY_DEBUG", "false").lower() in {"1", "true", "yes"},
            model=(
                os.getenv("CUTY_GEMINI_MODEL", "gemini-3.8-live")
                if provider == "gemini"
                else os.getenv("CUTY_REALTIME_MODEL", "gpt-realtime-2.1")
            ),
        )

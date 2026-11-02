import pytest

from cuty.config import Config, ConfigurationError


def test_missing_key(monkeypatch):
    monkeypatch.setenv("CUTY_AI_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ConfigurationError, match="GEMINI_API_KEY"):
        Config.from_env()


@pytest.mark.parametrize("placeholder", ["your_key_here", "YOUR_REAL_KEY", "sk-your-real-key"])
def test_placeholder_key(monkeypatch, placeholder):
    monkeypatch.setenv("CUTY_AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", placeholder)
    with pytest.raises(ConfigurationError, match="example placeholder"):
        Config.from_env()


def test_config_defaults_and_devices(monkeypatch):
    monkeypatch.setenv("CUTY_AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret")
    monkeypatch.setenv("CUTY_AUDIO_INPUT_DEVICE", "3")
    monkeypatch.setenv("CUTY_AUDIO_OUTPUT_DEVICE", "Speakers")
    config = Config.from_env()
    assert config.provider == "gemini"
    assert config.model == "gemini-3.8-live"
    assert config.input_device == "3"
    assert config.output_device == "Speakers"


def test_invalid_log_level(monkeypatch):
    monkeypatch.setenv("CUTY_AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret")
    monkeypatch.setenv("CUTY_LOG_LEVEL", "VERBOSE")
    with pytest.raises(ConfigurationError, match="CUTY_LOG_LEVEL"):
        Config.from_env()


def test_openai_remains_optional(monkeypatch):
    monkeypatch.setenv("CUTY_AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    config = Config.from_env()
    assert config.provider == "openai"
    assert config.model == "gpt-realtime-2.1"


def test_invalid_provider(monkeypatch):
    monkeypatch.setenv("CUTY_AI_PROVIDER", "unknown")
    with pytest.raises(ConfigurationError, match="CUTY_AI_PROVIDER"):
        Config.from_env()

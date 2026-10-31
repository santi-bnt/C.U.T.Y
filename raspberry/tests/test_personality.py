from cuty.brain.personality import INSTRUCTIONS, WEB_INSTRUCTIONS
from cuty.llm.gemini_provider import _CONFIG
import cuty.llm.openai_provider as openai_provider


def test_language_matching_instructions_reach_both_providers():
    assert "Match the language of the user's latest spoken turn automatically" in INSTRUCTIONS
    assert "Re-evaluate the language on every turn" in INSTRUCTIONS
    assert "An explicit request to answer in a particular language takes priority" in INSTRUCTIONS
    assert "Respond in Spanish unless" not in INSTRUCTIONS
    assert _CONFIG["system_instruction"] == INSTRUCTIONS + WEB_INSTRUCTIONS
    assert openai_provider.INSTRUCTIONS == INSTRUCTIONS

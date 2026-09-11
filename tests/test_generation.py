import pytest
from unittest.mock import MagicMock
from src.generation.prompt import build_prompt, SYSTEM_INSTRUCTION
from src.generation.llm import LLMClient
from src.generation.generator import ResponseGenerator, generate_reply

def test_prompt_construction():
    incoming = "Can we move our meeting to 3 PM today?"
    examples = [
        {
            "id": "EML-0001",
            "category": "Scheduling",
            "incoming_email": "Can we reschedule our sync?",
            "reference_reply": "Sure, 3 PM works fine."
        }
    ]
    prompt = build_prompt(incoming, examples)
    
    assert "HISTORICAL REFERENCE EXAMPLES:" in prompt
    assert "Example 1 [Scheduling]" in prompt
    assert "Can we reschedule our sync?" in prompt
    assert "Sure, 3 PM works fine." in prompt
    assert "NEW INCOMING EMAIL:" in prompt
    assert "Can we move our meeting to 3 PM today?" in prompt

def test_empty_email_validation():
    generator = ResponseGenerator(llm_client=MagicMock())
    with pytest.raises(ValueError, match="Incoming email cannot be empty."):
        generator.generate_reply("")
        
    with pytest.raises(ValueError, match="Incoming email cannot be empty."):
        generator.generate_reply("   ")

def test_missing_api_key_error():
    client = LLMClient(api_key="")
    with pytest.raises(ValueError, match="LLM API key is missing"):
        client.generate(SYSTEM_INSTRUCTION, "Test prompt")

def test_generator_with_mock_llm():
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = "Hi, 3 PM works great for our meeting. See you then!"
    
    generator = ResponseGenerator(llm_client=mock_llm)
    result = generator.generate_reply("Hi, can we meet at 3 PM today to discuss project updates?")
    
    assert "suggested_reply" in result
    assert result["suggested_reply"] == "Hi, 3 PM works great for our meeting. See you then!"
    assert "retrieved_examples" in result
    assert len(result["retrieved_examples"]) == 3
    mock_llm.generate.assert_called_once()

def test_invalid_llm_response_error():
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.side_effect = ValueError("LLM returned an empty or invalid response.")
    
    generator = ResponseGenerator(llm_client=mock_llm)
    with pytest.raises(ValueError, match="LLM returned an empty or invalid response."):
        generator.generate_reply("Need access to repo")

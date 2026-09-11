from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from api.main import app, pipeline
from src.generation.llm import LLMClient

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_generate_endpoint():
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = "Hello, Thursday at 2 PM works fine for our call."
    pipeline.generator.llm_client = mock_llm

    payload = {"email": "Hi, can we schedule a meeting on Thursday at 2 PM?"}
    response = client.post("/generate", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "suggested_reply" in data
    assert data["suggested_reply"] == "Hello, Thursday at 2 PM works fine for our call."
    assert "retrieved_examples" in data
    assert len(data["retrieved_examples"]) == 3

def test_generate_endpoint_empty_email():
    payload = {"email": "   "}
    response = client.post("/generate", json=payload)
    assert response.status_code == 400

def test_evaluate_endpoint():
    mock_llm = MagicMock(spec=LLMClient)
    pipeline.evaluator.llm_client = mock_llm

    payload = {
        "incoming_email": "Hi, can we meet on Thursday?",
        "generated_response": "Hi, Thursday works fine.",
        "reference_reply": "Hi, Thursday works fine."
    }
    response = client.post("/evaluate", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert "semantic_similarity" in data
    assert "relevance" in data
    assert "completeness" in data
    assert "tone" in data
    assert "factual_consistency" in data

def test_generate_and_evaluate_endpoint():
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = "Hi, invoice #123 has been received."
    pipeline.generator.llm_client = mock_llm
    pipeline.evaluator.llm_client = mock_llm

    payload = {
        "incoming_email": "Hi, please confirm receipt of invoice #123.",
        "reference_reply": "Hi, invoice #123 has been received."
    }
    response = client.post("/generate-and-evaluate", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "suggested_reply" in data
    assert "evaluation" in data
    assert data["evaluation"]["overall_score"] >= 0.0

def test_root_frontend_route():
    response = client.get("/")
    assert response.status_code == 200

import pytest
from src.evaluation.evaluator import evaluate_response

@pytest.fixture
def base_context():
    return {
        "incoming_email": "Hi Alice, could we schedule a 30-minute meeting on Thursday at 2 PM to review order #54321? Thanks, Bob.",
        "reference_reply": "Hi Bob, Thursday at 2 PM works great for me to review order #54321. I'll send over the calendar invite. Best, Alice."
    }

def test_good_response(base_context):
    good_gen = "Hi Bob, Thursday at 2 PM works fine to discuss order #54321. I'll send an invite shortly. Thanks, Alice."
    result = evaluate_response(
        incoming_email=base_context["incoming_email"],
        generated_response=good_gen,
        reference_reply=base_context["reference_reply"]
    )

    assert result["overall_score"] >= 75.0
    assert result["relevance"]["score"] >= 70.0
    assert result["factual_consistency"]["score"] >= 70.0

def test_irrelevant_response(base_context):
    irrelevant_gen = "I love eating pizza on Friday nights. What is your favorite movie genre?"
    result = evaluate_response(
        incoming_email=base_context["incoming_email"],
        generated_response=irrelevant_gen,
        reference_reply=base_context["reference_reply"]
    )

    assert result["overall_score"] < 60.0
    assert result["relevance"]["score"] < 50.0

def test_incomplete_response(base_context):
    incomplete_gen = "Hi Bob."
    result = evaluate_response(
        incoming_email=base_context["incoming_email"],
        generated_response=incomplete_gen,
        reference_reply=base_context["reference_reply"]
    )

    assert result["overall_score"] < 70.0
    assert result["completeness"]["score"] < 60.0

def test_contradictory_response(base_context):
    contradictory_gen = "Hi Bob, I cannot meet on Thursday at 2 PM, but I can do Friday for order #99999."
    result = evaluate_response(
        incoming_email=base_context["incoming_email"],
        generated_response=contradictory_gen,
        reference_reply=base_context["reference_reply"]
    )

    # Factuality or semantic should penalize order number / date contradiction
    assert result["factual_consistency"]["score"] < 60.0 or result["semantic_similarity"]["score"] < 70.0

def test_unprofessional_response(base_context):
    unprofessional_gen = "Nah dude, whatever. Stop bothering me about order #54321. Shut up."
    result = evaluate_response(
        incoming_email=base_context["incoming_email"],
        generated_response=unprofessional_gen,
        reference_reply=base_context["reference_reply"]
    )

    assert result["tone"]["score"] <= 40.0
    assert result["overall_score"] < 60.0

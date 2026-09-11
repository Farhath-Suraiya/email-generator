from typing import Dict, Any, Optional
from src.generation.llm import LLMClient
from src.evaluation.llm_base import LLMDimensionEvaluator
from src.evaluation.schemas import DimensionEvaluation

SYSTEM_PROMPT = """You are a strict email evaluation judge assessing COMPLETENESS.
Determine whether all important requests, questions, or call-to-actions in the incoming email are addressed by the generated response.

Evaluation Criteria:
- Score 90-100: All questions/requests in the incoming email are fully answered.
- Score 50-89: Some questions/requests are answered, but at least one important detail was missed.
- Score 0-49: Major questions/requests are ignored or missing entirely.

Respond strictly in valid JSON format with NO additional commentary:
{
  "score": <number 0-100>,
  "explanation": "<short clear summary>",
  "strengths": ["<strength 1>", ...],
  "issues": ["<issue 1>", ...]
}"""

class CompletenessEvaluator(LLMDimensionEvaluator):
    def evaluate(self, incoming_email: str, generated_response: str) -> Dict[str, Any]:
        if not generated_response.strip():
            return DimensionEvaluation(
                score=0.0,
                explanation="Generated response is empty.",
                strengths=[],
                issues=["Response body is blank."]
            ).model_dump()

        user_prompt = f"""INCOMING EMAIL:
{incoming_email.strip()}

GENERATED RESPONSE:
{generated_response.strip()}"""

        try:
            raw_response = self.llm_client.generate(
                system_instruction=SYSTEM_PROMPT,
                user_prompt=user_prompt
            )
            return self._parse_llm_json(raw_response)
        except Exception as e:
            return self._heuristic_fallback(incoming_email, generated_response)

    def _heuristic_fallback(self, incoming_email: str, generated_response: str) -> Dict[str, Any]:
        has_question = "?" in incoming_email
        gen_len = len(generated_response.strip().split())
        
        if has_question and gen_len < 5:
            score = 40.0
            explanation = "Incoming email contains questions but generated response is too brief."
            strengths = []
            issues = ["Questions in incoming email were not thoroughly addressed."]
        else:
            score = 80.0
            explanation = "Response addresses the incoming message length adequately."
            strengths = ["Sufficient detail provided."]
            issues = []

        return DimensionEvaluation(
            score=score,
            explanation=f"{explanation} (Evaluated via rule fallback)",
            strengths=strengths,
            issues=issues
        ).model_dump()

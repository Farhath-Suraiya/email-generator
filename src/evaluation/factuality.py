from typing import Dict, Any, Optional
from src.generation.llm import LLMClient
from src.evaluation.llm_base import LLMDimensionEvaluator
from src.evaluation.schemas import DimensionEvaluation

SYSTEM_PROMPT = """You are a strict email evaluation judge assessing FACTUAL CONSISTENCY.
Check whether the generated response contradicts any dates, times, names, invoice IDs, or explicit facts present in the incoming email or reference reply.

Evaluation Criteria:
- Score 90-100: Completely consistent with incoming facts and reference reply. No contradictions or invented facts.
- Score 50-89: Minor ambiguity, unverified assumption, or slight mismatch in non-critical detail.
- Score 0-49: Direct contradiction of dates, times, names, order numbers, or explicit facts.

Respond strictly in valid JSON format with NO additional commentary:
{
  "score": <number 0-100>,
  "explanation": "<short clear summary>",
  "strengths": ["<strength 1>", ...],
  "issues": ["<issue 1>", ...]
}"""

class FactualityEvaluator(LLMDimensionEvaluator):
    def evaluate(self, incoming_email: str, generated_response: str, reference_reply: str) -> Dict[str, Any]:
        if not generated_response.strip():
            return DimensionEvaluation(
                score=0.0,
                explanation="Generated response is empty.",
                strengths=[],
                issues=["Response body is blank."]
            ).model_dump()

        user_prompt = f"""INCOMING EMAIL:
{incoming_email.strip()}

REFERENCE REPLY:
{reference_reply.strip()}

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
        # Basic check for date/time/number contradictions
        import re
        inc_nums = set(re.findall(r'\b\d+\b', incoming_email))
        gen_nums = set(re.findall(r'\b\d+\b', generated_response))
        
        contradicted_nums = [n for n in gen_nums if n not in inc_nums and len(n) >= 3]

        if contradicted_nums:
            score = 40.0
            explanation = f"Generated response introduces unverified numbers/IDs: {', '.join(contradicted_nums[:3])}"
            strengths = []
            issues = [f"Contains numerical identifiers not present in incoming email: {', '.join(contradicted_nums[:3])}"]
        else:
            score = 90.0
            explanation = "No numerical contradictions detected."
            strengths = ["Preserves numerical identifiers correctly."]
            issues = []

        return DimensionEvaluation(
            score=score,
            explanation=f"{explanation} (Evaluated via rule fallback)",
            strengths=strengths,
            issues=issues
        ).model_dump()

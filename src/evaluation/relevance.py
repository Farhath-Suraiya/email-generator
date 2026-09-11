from typing import Dict, Any, Optional
from src.generation.llm import LLMClient
from src.evaluation.llm_base import LLMDimensionEvaluator
from src.evaluation.schemas import DimensionEvaluation

SYSTEM_PROMPT = """You are a strict email evaluation judge assessing RELEVANCE.
Determine whether the generated response directly addresses the incoming email request or topic.

Evaluation Criteria:
- Score 90-100: The response directly addresses the incoming email topic and key questions.
- Score 50-89: The response partially addresses the incoming email but omits core aspects.
- Score 0-49: The response is off-topic, generic, or ignores the incoming email's intent.

Respond strictly in valid JSON format with NO additional commentary:
{
  "score": <number 0-100>,
  "explanation": "<short clear summary>",
  "strengths": ["<strength 1>", ...],
  "issues": ["<issue 1>", ...]
}"""

class RelevanceEvaluator(LLMDimensionEvaluator):
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
            # Rule-based fallback if LLM API is unavailable
            return self._heuristic_fallback(incoming_email, generated_response, str(e))

    def _heuristic_fallback(self, incoming_email: str, generated_response: str, err_msg: str) -> Dict[str, Any]:
        inc_words = set(incoming_email.lower().split())
        gen_words = set(generated_response.lower().split())
        overlap = len(inc_words.intersection(gen_words)) / (len(inc_words) + 1e-5)
        
        if overlap > 0.15:
            score, exp = 85.0, "Response appears relevant to the incoming email topics."
            strengths, issues = ["Overlapping key topics detected."], []
        else:
            score, exp = 30.0, "Response shows minimal topical overlap with incoming email."
            strengths, issues = [], ["Low topical keyword overlap."]

        return DimensionEvaluation(
            score=score,
            explanation=f"{exp} (Evaluated via rule fallback)",
            strengths=strengths,
            issues=issues
        ).model_dump()

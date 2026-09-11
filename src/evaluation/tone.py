from typing import Dict, Any, Optional
from src.generation.llm import LLMClient
from src.evaluation.llm_base import LLMDimensionEvaluator
from src.evaluation.schemas import DimensionEvaluation

SYSTEM_PROMPT = """You are a strict email evaluation judge assessing PROFESSIONAL TONE.
Evaluate whether the generated response is polite, professional, and workplace-appropriate.

Evaluation Criteria:
- Score 90-100: Polished, professional, courteous, and highly appropriate tone.
- Score 50-89: Generally acceptable tone, but slightly informal, blunt, or overly casual.
- Score 0-49: Unprofessional, rude, hostile, or inappropriately informal.

Respond strictly in valid JSON format with NO additional commentary:
{
  "score": <number 0-100>,
  "explanation": "<short clear summary>",
  "strengths": ["<strength 1>", ...],
  "issues": ["<issue 1>", ...]
}"""

class ToneEvaluator(LLMDimensionEvaluator):
    def evaluate(self, generated_response: str) -> Dict[str, Any]:
        if not generated_response.strip():
            return DimensionEvaluation(
                score=0.0,
                explanation="Generated response is empty.",
                strengths=[],
                issues=["Response body is blank."]
            ).model_dump()

        user_prompt = f"""GENERATED RESPONSE:
{generated_response.strip()}"""

        try:
            raw_response = self.llm_client.generate(
                system_instruction=SYSTEM_PROMPT,
                user_prompt=user_prompt
            )
            return self._parse_llm_json(raw_response)
        except Exception as e:
            return self._heuristic_fallback(generated_response)

    def _heuristic_fallback(self, generated_response: str) -> Dict[str, Any]:
        lower = generated_response.lower()
        unprofessional_words = ["nah", "whatever", "dude", "nope", "shut up", "idiot", "crap", "hate"]
        polite_words = ["thanks", "thank you", "best", "regards", "please", "hello", "hi", "sincerely"]
        
        has_unprofessional = any(w in lower for w in unprofessional_words)
        has_polite = any(w in lower for w in polite_words)

        if has_unprofessional:
            score = 30.0
            explanation = "Response contains informal or unprofessional wording."
            strengths = []
            issues = ["Contains casual or unprofessional language."]
        elif has_polite:
            score = 90.0
            explanation = "Response contains polite business greetings and closings."
            strengths = ["Professional salutations and polite phrasing."]
            issues = []
        else:
            score = 70.0
            explanation = "Neutral tone with no explicit greetings or profanity."
            strengths = []
            issues = []

        return DimensionEvaluation(
            score=score,
            explanation=f"{explanation} (Evaluated via rule fallback)",
            strengths=strengths,
            issues=issues
        ).model_dump()

import json
import re
from typing import Dict, Any, Optional
from src.generation.llm import LLMClient
from src.evaluation.schemas import DimensionEvaluation

class LLMDimensionEvaluator:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def _parse_llm_json(self, response_text: str) -> Dict[str, Any]:
        cleaned = response_text.strip()
        # Remove markdown block backticks if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
            return DimensionEvaluation(**data).model_dump()
        except Exception:
            # Fallback if JSON parsing fails
            return DimensionEvaluation(
                score=50.0,
                explanation="Failed to parse structured evaluation JSON output.",
                strengths=[],
                issues=["Invalid format returned by evaluation LLM."]
            ).model_dump()

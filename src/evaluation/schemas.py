from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator

class DimensionEvaluation(BaseModel):
    score: float = Field(..., description="Score from 0.0 to 100.0")
    explanation: str = Field(..., description="Concise explanation of the score")
    strengths: List[str] = Field(default_factory=list, description="Key strengths identified")
    issues: List[str] = Field(default_factory=list, description="Key issues or gaps identified")

    @field_validator("score")
    @classmethod
    def clamp_score(cls, v: float) -> float:
        return max(0.0, min(100.0, round(float(v), 2)))

class FullEvaluationResult(BaseModel):
    semantic_similarity: DimensionEvaluation
    relevance: DimensionEvaluation
    completeness: DimensionEvaluation
    tone: DimensionEvaluation
    factual_consistency: DimensionEvaluation
    overall_score: float = Field(..., description="Weighted overall quality score from 0 to 100")
    overall_explanation: str = Field(..., description="Overall summary of response quality")
    strengths: List[str] = Field(default_factory=list, description="Aggregated key strengths")
    issues: List[str] = Field(default_factory=list, description="Aggregated key issues")

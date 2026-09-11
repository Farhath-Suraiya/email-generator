import numpy as np
from typing import Dict, Any, Optional
from src.retrieval.embeddings import EmbeddingGenerator
from src.evaluation.schemas import DimensionEvaluation

class SemanticEvaluator:
    def __init__(self, embedding_generator: Optional[EmbeddingGenerator] = None):
        self.embedding_generator = embedding_generator or EmbeddingGenerator()

    def evaluate(self, generated_response: str, reference_reply: str) -> Dict[str, Any]:
        if not generated_response.strip() or not reference_reply.strip():
            return DimensionEvaluation(
                score=0.0,
                explanation="Response or reference reply is empty.",
                strengths=[],
                issues=["Empty text provided for semantic comparison."]
            ).model_dump()

        emb_gen = self.embedding_generator.encode(generated_response, normalize=True)
        emb_ref = self.embedding_generator.encode(reference_reply, normalize=True)

        # Dot product of normalized vectors = Cosine similarity
        cosine_sim = float(np.dot(emb_gen[0], emb_ref[0]))
        score = max(0.0, min(100.0, round(cosine_sim * 100.0, 2)))

        strengths = []
        issues = []

        if score >= 80:
            explanation = "High semantic alignment with the reference response."
            strengths.append("Captures similar intent and core message of reference reply.")
        elif score >= 50:
            explanation = "Moderate semantic alignment with the reference response."
            issues.append("Slight divergence in wording or structure from reference reply.")
        else:
            explanation = "Low semantic alignment with the reference response."
            issues.append("Significant semantic divergence from reference reply.")

        return DimensionEvaluation(
            score=score,
            explanation=explanation,
            strengths=strengths,
            issues=issues
        ).model_dump()

from typing import Dict, Any, Optional
from src.generation.llm import LLMClient
from src.retrieval.embeddings import EmbeddingGenerator
from src.evaluation.semantic import SemanticEvaluator
from src.evaluation.relevance import RelevanceEvaluator
from src.evaluation.completeness import CompletenessEvaluator
from src.evaluation.tone import ToneEvaluator
from src.evaluation.factuality import FactualityEvaluator
from src.evaluation.schemas import FullEvaluationResult

class EmailResponseEvaluator:
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None
    ):
        self.llm_client = llm_client or LLMClient()
        self.semantic_evaluator = SemanticEvaluator(embedding_generator=embedding_generator)
        self.relevance_evaluator = RelevanceEvaluator(llm_client=self.llm_client)
        self.completeness_evaluator = CompletenessEvaluator(llm_client=self.llm_client)
        self.tone_evaluator = ToneEvaluator(llm_client=self.llm_client)
        self.factuality_evaluator = FactualityEvaluator(llm_client=self.llm_client)

    def evaluate_response(
        self,
        incoming_email: str,
        generated_response: str,
        reference_reply: str
    ) -> Dict[str, Any]:
        # 1. Evaluate individual dimensions
        sem_res = self.semantic_evaluator.evaluate(generated_response, reference_reply)
        rel_res = self.relevance_evaluator.evaluate(incoming_email, generated_response)
        comp_res = self.completeness_evaluator.evaluate(incoming_email, generated_response)
        tone_res = self.tone_evaluator.evaluate(generated_response)
        fact_res = self.factuality_evaluator.evaluate(incoming_email, generated_response, reference_reply)

        # 2. Weighted overall score calculation
        # overall = 0.25 * semantic_similarity + 0.20 * relevance + 0.20 * completeness + 0.15 * tone + 0.20 * factual_consistency
        overall_score = round(
            0.25 * sem_res["score"] +
            0.20 * rel_res["score"] +
            0.20 * comp_res["score"] +
            0.15 * tone_res["score"] +
            0.20 * fact_res["score"],
            2
        )

        # 3. Aggregate strengths and issues
        all_strengths = set(
            sem_res["strengths"] +
            rel_res["strengths"] +
            comp_res["strengths"] +
            tone_res["strengths"] +
            fact_res["strengths"]
        )
        all_issues = set(
            sem_res["issues"] +
            rel_res["issues"] +
            comp_res["issues"] +
            tone_res["issues"] +
            fact_res["issues"]
        )

        # 4. Generate summary explanation
        if overall_score >= 85:
            overall_explanation = f"High quality response (score: {overall_score}/100). Well-aligned, complete, polite, and factually accurate."
        elif overall_score >= 60:
            overall_explanation = f"Acceptable response (score: {overall_score}/100) with minor gaps or stylistic differences."
        else:
            overall_explanation = f"Low quality response (score: {overall_score}/100). Contains significant issues in relevance, completeness, tone, or factuality."

        result = FullEvaluationResult(
            semantic_similarity=sem_res,
            relevance=rel_res,
            completeness=comp_res,
            tone=tone_res,
            factual_consistency=fact_res,
            overall_score=overall_score,
            overall_explanation=overall_explanation,
            strengths=sorted(list(all_strengths)),
            issues=sorted(list(all_issues))
        )

        return result.model_dump()

# Convenience standalone function interface
def evaluate_response(
    incoming_email: str,
    generated_response: str,
    reference_reply: str,
    llm_client: Optional[LLMClient] = None,
    embedding_generator: Optional[EmbeddingGenerator] = None
) -> Dict[str, Any]:
    evaluator = EmailResponseEvaluator(llm_client=llm_client, embedding_generator=embedding_generator)
    return evaluator.evaluate_response(
        incoming_email=incoming_email,
        generated_response=generated_response,
        reference_reply=reference_reply
    )

from typing import Dict, Any, Optional
from src.retrieval.retriever import EmailRetriever
from src.generation.generator import ResponseGenerator
from src.generation.llm import LLMClient
from src.evaluation.evaluator import EmailResponseEvaluator

class EmailResponsePipeline:
    def __init__(
        self,
        retriever: Optional[EmailRetriever] = None,
        generator: Optional[ResponseGenerator] = None,
        evaluator: Optional[EmailResponseEvaluator] = None,
        llm_client: Optional[LLMClient] = None
    ):
        self.llm_client = llm_client or LLMClient()
        self.retriever = retriever or EmailRetriever()
        self.generator = generator or ResponseGenerator(llm_client=self.llm_client)
        self.evaluator = evaluator or EmailResponseEvaluator(llm_client=self.llm_client)

    def generate_response(self, incoming_email: str, top_k: int = 3) -> Dict[str, Any]:
        """Mode A — Generation only."""
        gen_result = self.generator.generate_reply(email=incoming_email, top_k=top_k)
        return {
            "incoming_email": incoming_email,
            "suggested_reply": gen_result["suggested_reply"],
            "retrieved_examples": gen_result["retrieved_examples"]
        }

    def process_and_evaluate(
        self,
        incoming_email: str,
        reference_reply: str,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """Mode B — Generation + Evaluation against reference reply."""
        if not reference_reply or not reference_reply.strip():
            raise ValueError("Reference reply must be provided for evaluation mode.")

        # Ensure reference reply is NOT passed to generation phase
        gen_result = self.generate_response(incoming_email=incoming_email, top_k=top_k)
        suggested_reply = gen_result["suggested_reply"]

        eval_result = self.evaluator.evaluate_response(
            incoming_email=incoming_email,
            generated_response=suggested_reply,
            reference_reply=reference_reply
        )

        return {
            "incoming_email": incoming_email,
            "reference_reply": reference_reply,
            "suggested_reply": suggested_reply,
            "retrieved_examples": gen_result["retrieved_examples"],
            "evaluation": eval_result
        }

    def process_email(
        self,
        incoming_email: str,
        reference_reply: Optional[str] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """Unified pipeline entrypoint supporting Mode A and Mode B."""
        if reference_reply and reference_reply.strip():
            return self.process_and_evaluate(incoming_email, reference_reply, top_k=top_k)
        return self.generate_response(incoming_email, top_k=top_k)

# Standalone helper function
def run_pipeline(
    incoming_email: str,
    reference_reply: Optional[str] = None,
    top_k: int = 3
) -> Dict[str, Any]:
    pipeline = EmailResponsePipeline()
    return pipeline.process_email(incoming_email=incoming_email, reference_reply=reference_reply, top_k=top_k)

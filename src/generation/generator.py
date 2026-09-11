from typing import Dict, Any, List, Optional
from src.retrieval.retriever import retrieve_similar_emails
from src.generation.prompt import SYSTEM_INSTRUCTION, build_prompt
from src.generation.llm import LLMClient

class ResponseGenerator:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def generate_reply(self, email: str, top_k: int = 3) -> Dict[str, Any]:
        if not email or not email.strip():
            raise ValueError("Incoming email cannot be empty.")

        # 1. Retrieve top-k relevant examples
        retrieved_examples: List[Dict[str, Any]] = retrieve_similar_emails(email=email, top_k=top_k)

        # 2. Build prompt
        prompt_text = build_prompt(incoming_email=email, retrieved_examples=retrieved_examples)

        # 3. Call LLM
        suggested_reply = self.llm_client.generate(
            system_instruction=SYSTEM_INSTRUCTION,
            user_prompt=prompt_text
        )

        return {
            "suggested_reply": suggested_reply,
            "retrieved_examples": retrieved_examples
        }

# Convenience standalone function
def generate_reply(email: str, top_k: int = 3, llm_client: Optional[LLMClient] = None) -> Dict[str, Any]:
    generator = ResponseGenerator(llm_client=llm_client)
    return generator.generate_reply(email=email, top_k=top_k)

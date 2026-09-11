from typing import List, Dict, Any

SYSTEM_INSTRUCTION = """You are an expert AI professional email assistant. Your task is to draft a clear, polite, and effective response to an incoming email.

GUIDELINES:
1. Directly address the incoming email request, query, or statement.
2. Use the provided historical email/reply examples ONLY as reference guidance for style, context, and expected action.
3. Do NOT blindly copy the reference replies word-for-word.
4. Do NOT invent facts, assumptions, or details not present in the incoming email or standard business context.
5. Accurately preserve all specific dates, times, names, invoice/order IDs, and requested actions mentioned in the incoming email.
6. Use professional, natural, and courteous business language.
7. Avoid meta-commentary, preamble, postscript, or explanations. Output ONLY the suggested email response body.
"""

def build_prompt(incoming_email: str, retrieved_examples: List[Dict[str, Any]]) -> str:
    examples_text = ""
    if retrieved_examples:
        for idx, ex in enumerate(retrieved_examples, 1):
            category = ex.get("category", "General")
            inc = ex.get("incoming_email", "").strip()
            ref = ex.get("reference_reply", "").strip()
            examples_text += f"--- Example {idx} [{category}] ---\nIncoming:\n{inc}\n\nReference Reply:\n{ref}\n\n"
    else:
        examples_text = "No historical examples available.\n\n"

    user_prompt = f"""HISTORICAL REFERENCE EXAMPLES:
{examples_text}NEW INCOMING EMAIL:
{incoming_email.strip()}

SUGGESTED EMAIL RESPONSE:"""
    
    return user_prompt

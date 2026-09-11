from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    email: str = Field(..., min_length=1, description="Incoming email text")

class GenerateResponse(BaseModel):
    suggested_reply: str
    retrieved_examples: List[Dict[str, Any]]

class EvaluateRequest(BaseModel):
    incoming_email: str = Field(..., min_length=1)
    generated_response: str = Field(..., min_length=1)
    reference_reply: str = Field(..., min_length=1)

class GenerateAndEvaluateRequest(BaseModel):
    incoming_email: str = Field(..., min_length=1)
    reference_reply: str = Field(..., min_length=1)

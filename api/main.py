import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.schemas import (
    GenerateRequest,
    GenerateResponse,
    EvaluateRequest,
    GenerateAndEvaluateRequest
)
from src.pipeline.email_pipeline import EmailResponsePipeline
from src.generation.generator import ResponseGenerator
from src.evaluation.evaluator import evaluate_response

app = FastAPI(
    title="AI Email Suggested-Response System API",
    description="Production-quality AI email suggested-response generation and multi-dimensional evaluation system.",
    version="1.0.0"
)

# Pipeline instances
pipeline = EmailResponsePipeline()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/generate", response_model=GenerateResponse)
def generate_reply_endpoint(req: GenerateRequest):
    if not req.email or not req.email.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incoming email cannot be empty.")
    
    try:
        res = pipeline.generate_response(incoming_email=req.email)
        return GenerateResponse(
            suggested_reply=res["suggested_reply"],
            retrieved_examples=res["retrieved_examples"]
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Generation failed: {str(e)}")

@app.post("/evaluate")
def evaluate_endpoint(req: EvaluateRequest):
    if not req.incoming_email.strip() or not req.generated_response.strip() or not req.reference_reply.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All evaluation fields must be non-empty.")
    
    try:
        eval_result = evaluate_response(
            incoming_email=req.incoming_email,
            generated_response=req.generated_response,
            reference_reply=req.reference_reply
        )
        return eval_result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Evaluation failed: {str(e)}")

@app.post("/generate-and-evaluate")
def generate_and_evaluate_endpoint(req: GenerateAndEvaluateRequest):
    if not req.incoming_email.strip() or not req.reference_reply.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incoming email and reference reply are required.")

    try:
        # Reference reply is strictly excluded from generation, only passed to evaluation
        result = pipeline.process_and_evaluate(
            incoming_email=req.incoming_email,
            reference_reply=req.reference_reply
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Pipeline execution failed: {str(e)}")

# Mount static files for frontend web interface
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def read_root():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "AI Email Suggested-Response API is running. Frontend static files pending."}

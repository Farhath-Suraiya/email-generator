# AI Email Suggested-Response System

A production-quality, end-to-end AI system that grounds email response generation on historical email context using Retrieval-Augmented Generation (RAG), vector similarity search, and multi-dimensional quality evaluation.

---

## Problem Statement

Modern professionals and customer-support teams receive hundreds of emails daily covering repetitive categories such as meeting requests, status updates, invoice confirmations, technical inquiries, and document requests. Manually drafting responses is time-consuming and prone to inconsistency. 

Classical Machine Learning classifiers can categorize emails but cannot generate rich, contextual, natural language replies. On the other hand, ungrounded Large Language Models (LLMs) often hallucinate facts, invent invalid dates or reference numbers, or fail to adhere to organizational communication style guidelines.

---

## Solution

The **AI Email Suggested-Response System** bridges this gap using a grounded Retrieval-Augmented Generation (RAG) architecture:
1. **Contextual Retrieval:** incoming emails trigger semantic similarity search over historical email–reply pairs using Sentence Transformers (`all-MiniLM-L6-v2`) and FAISS vector indices.
2. **Grounded LLM Generation:** top-$k$ retrieved historical pairs are injected as reference guidance into an LLM prompt (`OpenAI` / `Google Gemini`), instructing the model to answer the query accurately while preserving specific dates, times, names, and IDs without hallucinating facts or blindly copying text.
3. **Multi-Dimensional Quality Evaluation:** an automated composite evaluator scores the generated response across 5 distinct dimensions (Semantic Similarity, Relevance, Completeness, Professional Tone, and Factual Consistency), producing normalized 0–100 quality scores, concise explanations, and actionable strengths/issues breakdowns.
4. **Human-in-the-Loop Web Interface:** a clean, responsive FastAPI + HTML/CSS/JS frontend provides real-time response generation, one-click copying, grounding context inspection, and evaluation visualization.

---

## Architecture

```
                                  +-----------------------+
                                  |    Incoming Email     |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |  Sentence Transformer |
                                  | (all-MiniLM-L6-v2)    |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |   FAISS Vector Index  |
                                  | (Train Data Only)     |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  | Top-3 Retrieved Pairs |
                                  +-----------+-----------+
                                              |
                                              v
+-----------------------+         +-----------+-----------+
|  System Instruction   | ------->|   Grounded Prompt     |
+-----------------------+         +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |       LLM API         |
                                  | (OpenAI / Gemini)     |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |   Suggested Response  |
                                  +-----------+-----------+
                                              |
   (If Reference Reply Provided) ------------>+
                                              |
                                              v
                                  +-----------+-----------+
                                  | Multi-Dim Evaluator   |
                                  | (5 Quality Metrics)   |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  | Response Quality Score|
                                  |  (0 - 100 Normalized) |
                                  +-----------------------+
```

---

## Dataset

### Dataset Source & Synthetic Nature
To avoid using confidential, private, or proprietary personal email data, this project uses a synthetically authored professional email dataset.

### Why Synthetic Professional Email Data?
Professional communication follows structured, recurring intent patterns across business domains (such as meeting scheduling, approvals, customer support, project updates, and technical inquiries). Synthetic dataset generation allows:
- **Full Privacy Compliance:** No PII, customer privacy violations, or NDA breaches.
- **Controlled Intent Coverage:** Balanced distribution across diverse communication intents, tones, urgency levels, and request types.
- **Clean Grounding Benchmark:** Consistent evaluation metrics free of external noisy data artifacts.

### Categories Covered (15 Domains)
1. **Meeting**: Aligning agendas, setting sync calls, confirming attendance.
2. **Scheduling**: Managing reschedules, calendar availability, interview loops.
3. **Customer Support**: Order inquiries, refund requests, account unlocks.
4. **Internship/Job**: Applications, interview follow-ups, offer acceptances.
5. **Leave Request**: Annual, sick, and emergency leave requests and approvals.
6. **Project Update**: Milestone reports, blocker alerts, release notifications.
7. **Document Request**: Sharing and requesting contracts, specs, financial reports.
8. **Follow-up**: Tracking pending proposals, tickets, decisions.
9. **Payment/Billing**: Invoices, billing inquiries, wire confirmations.
10. **Technical Issue**: Outages, SSH timeouts, pipeline errors.
11. **Apology**: Professional apologies for missed calls or oversights.
12. **Confirmation**: Confirming document receipt or payment settlements.
13. **Invitation**: Event invitations, speaker invites, beta testing requests.
14. **Information Request**: Inquiring about service tiers, SLAs, specs.
15. **Professional Networking**: Intro calls, conference connections, alumni networking.

### Dataset Splits & Data Leakage Prevention
- **Total Records:** 720 unique email/reply pairs.
- **Train (70% - 503 records):** Used exclusively for building the FAISS vector index.
- **Validation (15% - 108 records):** Used for prompt tuning and hyperparameter adjustment.
- **Test (15% - 109 records):** Reserved strictly for evaluation benchmarking.

> [!IMPORTANT]
> **Data Leakage Rule:** Test dataset records are strictly excluded from the FAISS vector retrieval index. Furthermore, during generation benchmarking, the test reference reply is **never** passed into the LLM generation prompt. It is only supplied to the evaluation engine after generation.

---

## Response Generation

- **Embeddings:** `all-MiniLM-L6-v2` generates 384-dimensional normalized vector embeddings for incoming email text.
- **Vector Search:** `faiss.IndexFlatIP` computes cosine similarity over normalized embeddings to fetch the top-$k$ ($k=3$) historical training pairs.
- **Prompt Grounding:** Retrieved examples are formatted into structured reference context alongside explicit guidelines:
  - Directly answer the incoming email.
  - Use historical examples for style/context guidance only.
  - Do NOT copy text word-for-word.
  - Preserve all dates, times, names, and order numbers accurately.
  - Do NOT invent unverified facts.
- **LLM Abstraction:** Supports configurable LLM providers (`OpenAI` / `Google Gemini`) managed via `.env` configuration.

---

## Why RAG? (Trade-off vs Fine-Tuning)

| Dimension | Fine-Tuning | Retrieval-Augmented Generation (RAG) |
| :--- | :--- | :--- |
| **Knowledge Updates** | Requires expensive retraining for new email templates/policies. | Instantly update index by adding new JSON records. |
| **Hallucination Control** | High risk of hallucinating outdated training facts. | Grounded in retrieved historical reference examples. |
| **Cost & Latency** | High computational cost for training and hosting custom weights. | Uses lightweight local vector index + fast standard API call. |
| **Auditability** | Black-box weights; hard to trace response rationale. | Transparent: displays exact top-$k$ retrieved historical context. |

---

## Evaluation

Traditional string matching metrics like exact match, BLEU, or ROUGE fail for email generation because semantically valid, professional replies can use completely different phrasing.

Our evaluation system measures quality across **5 weighted dimensions**, normalizing scores from 0 to 100:

1. **Semantic Similarity (25%):** Embedding cosine similarity between generated response and reference reply.
2. **Relevance (20%):** Evaluates whether the response directly addresses the incoming email topic.
3. **Completeness (20%):** Evaluates whether all questions and requested actions are addressed.
4. **Professional Tone (15%):** Evaluates politeness, professional language, and workplace appropriateness.
5. **Factual Consistency (20%):** Checks for numerical or factual contradictions (dates, times, names, order IDs).

### Overall Weighted Quality Score
$$\text{Overall Score} = 0.25 \times \text{Semantic} + 0.20 \times \text{Relevance} + 0.20 \times \text{Completeness} + 0.15 \times \text{Tone} + 0.20 \times \text{Factuality}$$

Each evaluation outputs structured JSON containing `score`, `explanation`, `strengths`, and `issues`.

---

## Evaluation Validation

To validate that the automated multi-dimensional evaluator aligns with human judgment:
- We established a human annotation framework in `src/evaluation/human_validation.py`.
- `data/human_annotations.json` provides an unannotated template of 60 candidate items awaiting manual 1–5 human quality ratings.
- The pipeline converts human 1–5 ratings to a 0–100 scale (`(score - 1) * 25`) and calculates:
  - **Pearson Correlation ($r$)**
  - **Spearman Rank Correlation ($\rho$)**
  - **Mean Absolute Error (MAE)**

> [!NOTE]
> Until human annotators submit ratings in `data/human_annotations.json`, the validation pipeline accurately reports `pending_annotations` status rather than fabricating artificial correlation values.

---

## Results

When running the benchmark pipeline (`python -m src.evaluation.run_benchmark`):
- Benchmark results are generated directly from the 109 holdout test records.
- Outputs are saved to:
  - `results/per_response_scores.json`
  - `results/per_response_scores.csv`
  - `results/evaluation_report.json`
  - `results/evaluation_report.md`

---

## Failure Analysis

The evaluation system detects and penalizes common failure modes:
1. **Irrelevant Response:** Replying with unrelated content (e.g., weather reports). *Penalized on Relevance (< 50) and Overall Score (< 60).*
2. **Incomplete Response:** Returning extremely brief or partial answers (e.g., "Hi."). *Penalized on Completeness (< 60).*
3. **Contradictory Response:** Inventing conflicting order numbers or dates. *Penalized on Factual Consistency (< 60).*
4. **Inappropriate Tone:** Using casual slang or rude language (e.g., "Nah dude, shut up."). *Penalized on Professional Tone (<= 40).*

---

## API Documentation

The FastAPI backend exposes the following REST endpoints:

### 1. Health Check
`GET /health`
```json
{
  "status": "ok"
}
```

### 2. Generate Suggested Reply
`POST /generate`

**Request:**
```json
{
  "email": "Hi Alice, could we schedule a 30-minute meeting on Thursday at 2 PM to review order #54321? Thanks, Bob."
}
```

**Response:**
```json
{
  "suggested_reply": "Hi Bob,\n\nThursday at 2 PM works great for me to review order #54321. I will send over a calendar invite shortly.\n\nBest regards,\nAlice",
  "retrieved_examples": [
    {
      "id": "EML-0012",
      "category": "Meeting",
      "incoming_email": "Hi Alice, can we set up a quick 30-minute sync regarding Q3 roadmap?",
      "reference_reply": "Hi Bob, I am available on Thursday between 2:00 PM - 4:00 PM...",
      "score": 0.884
    }
  ]
}
```

### 3. Evaluate Response
`POST /evaluate`

**Request:**
```json
{
  "incoming_email": "Hi Alice, could we schedule a meeting on Thursday at 2 PM?",
  "generated_response": "Hi Bob, Thursday at 2 PM works fine.",
  "reference_reply": "Hi Bob, Thursday at 2 PM works great for me."
}
```

### 4. Generate and Evaluate (Benchmark / Demo Mode)
`POST /generate-and-evaluate`

**Request:**
```json
{
  "incoming_email": "Hi Alice, could we schedule a meeting on Thursday at 2 PM?",
  "reference_reply": "Hi Bob, Thursday at 2 PM works great for me."
}
```

---

## How to Run

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone & Set Up Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure LLM API Key
Edit `.env` and configure your LLM provider and API key:
```ini
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini
```

### 3. Execute Data & Index Pipelines

```bash
# 1. Generate synthetic email dataset (data/raw/emails.json)
python src/data/generate_dataset.py

# 2. Validate & split dataset (data/processed/train.json, val.json, test.json)
python src/data/prepare_dataset.py

# 3. Build FAISS vector index (data/index/faiss_index.bin)
python -m src.retrieval.index
```

### 4. Run Tests & Demos

```bash
# Run pytest test suite (29/29 unit tests)
python -m pytest tests/

# Run single pipeline demo
python -m src.pipeline.run_demo

# Run benchmark on test dataset
python -m src.evaluation.run_benchmark
```

### 5. Launch FastAPI Backend & Web Frontend

```bash
uvicorn api.main:app --reload
```

Open your browser and navigate to `http://127.0.0.1:8000/` to access the interactive web interface.

---

## Project Structure

```
email-response-ai/
├── data/
│   ├── raw/
│   │   └── README.md
│   ├── processed/
│   ├── index/
│   ├── human_annotations.json
│   └── README.md
├── src/
│   ├── data/
│   │   ├── __init__.py
│   │   ├── generate_dataset.py
│   │   └── prepare_dataset.py
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── embeddings.py
│   │   ├── index.py
│   │   └── retriever.py
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── prompt.py
│   │   ├── llm.py
│   │   └── generator.py
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── semantic.py
│   │   ├── relevance.py
│   │   ├── completeness.py
│   │   ├── tone.py
│   │   ├── factuality.py
│   │   ├── llm_base.py
│   │   ├── evaluator.py
│   │   ├── human_validation.py
│   │   └── run_benchmark.py
│   └── pipeline/
│       ├── __init__.py
│       ├── email_pipeline.py
│       └── run_demo.py
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── schemas.py
│   └── static/
│       ├── index.html
│       ├── style.css
│       └── app.js
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_retrieval.py
│   ├── test_generation.py
│   ├── test_evaluation.py
│   ├── test_pipeline.py
│   ├── test_human_validation.py
│   └── test_benchmark.py
├── results/
│   └── README.md
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Limitations

- **Synthetic Dataset Scope:** While representative of professional scenarios, synthetic data cannot capture all domain-specific jargon of specialized industries.
- **LLM API Dependency:** Generation quality and latency depend on the upstream LLM provider availability.
- **Evaluation Heuristics:** Automated LLM evaluation dimensions require a valid API key for LLM-based judges; fallback rules are used in offline environments.
- **Human Annotation Requirement:** Correlation metrics are only calculated after human annotators complete ratings in `data/human_annotations.json`.

---

## AI Tools Used

AI coding assistants (Google Antigravity / Gemini) were utilized for:
- Code scaffolding and directory boilerplate creation
- Refactoring PyTorch CPU multi-threading parameters
- Iterating prompt template instructions
- Synthetic email dataset generation scripting
- Generating Markdown project documentation

*All generated code, schemas, unit tests, and pipeline outputs were manually verified, tested, and validated.*

---

## Reproducibility

To reproduce all results from scratch:
1. Clone the repository into a clean environment.
2. Install dependencies via `pip install -r requirements.txt`.
3. Set your API key in `.env`.
4. Run dataset generation, dataset preparation, and index building commands listed in [How to Run](#how-to-run).
5. Run `python -m pytest tests/` to verify all 29 unit tests pass cleanly.

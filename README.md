# ✨ IntelliPrompt

**An Adaptive Prompt Optimization and Model-Adaptive Prompt Translation Framework for Multi-LLM Systems**

IntelliPrompt automatically transforms rough, poorly structured user prompts into high-quality, optimized prompts tailored for specific Large Language Models — no prompt engineering expertise required.

---

## The Problem

Most users struggle to write effective prompts. A prompt that works well for ChatGPT may perform poorly on Claude or Gemini because each model is trained differently and responds to different structures and styles. Users spend significant time manually rewriting prompts with little guidance.

---

## The Solution

IntelliPrompt solves this with two core engines:

### ⚙️ AMPOA — Adaptive Multi-stage Prompt Optimization Algorithm
A 7-stage rule-based pipeline that transforms any raw prompt into a structured, universal prompt:

| Stage | What it does |
|-------|-------------|
| 1. Clean | Remove noise, fix punctuation, normalize text |
| 2. Intent Detection | Classify as explain / generate / analyze / debug / summarize… |
| 3. Domain Detection | Identify technology / science / business / healthcare… |
| 4. Entity Extraction | Extract key concepts and terms |
| 5. Context Enrichment | Add domain-specific framing phrases |
| 6. Prompt Expansion | Add clarity directives based on detected intent |
| 7. Structuring | Format into Role · Task · Context · Constraints · Output Format |

### 🔄 MAPT — Model-Adaptive Prompt Translation
Adapts the universal prompt to each LLM's preferred style:

| LLM | Adaptation Style |
|-----|-----------------|
| Claude (Anthropic) | XML tags `<task>` `<context>` `<instructions>` · step-by-step reasoning |
| ChatGPT (OpenAI) | Role assignment · numbered steps · structured sections |
| Gemini (Google) | Bold headers · bullet points · concise framing |
| DeepSeek | Technical precision · markdown hints · code-friendly format |

### 📊 Quality Scoring
Every optimized prompt is scored out of **100** across 5 dimensions:
- **Clarity** (25%) — readability, sentence structure, action words
- **Specificity** (25%) — detail level, numbers, technical terms
- **Completeness** (20%) — role, context, task, output format hints
- **Context** (15%) — domain vocabulary, background information
- **Actionability** (15%) — clear deliverable, action verb, measurable outcome

Grade scale: **A** ≥85 · **B** ≥70 · **C** ≥55 · **D** ≥40 · **F** <40

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend | FastAPI |
| Language | Python 3.12 |
| ORM | SQLAlchemy |
| Database | SQLite (dev) |
| LLM API | OpenRouter |
| Deployment | Streamlit Cloud + Render |

---

## Project Structure

```
Inteliprompt/
├── backend/
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Environment settings
│   ├── database.py           # SQLAlchemy setup
│   ├── models/               # ORM models
│   ├── schemas/              # Pydantic schemas
│   ├── routers/              # API route handlers
│   │   ├── prompt.py         # POST /prompt/optimize
│   │   └── history.py        # GET/DELETE /history
│   └── services/
│       ├── ampoa.py          # AMPOA engine (7-stage pipeline)
│       ├── mapt.py           # MAPT engine (4 LLM adapters)
│       └── scoring.py        # Prompt quality scorer
├── frontend/
│   ├── app.py                # Streamlit chat interface
│   └── utils/
│       └── api_client.py     # Backend API client
├── requirements.txt
├── render.yaml               # Render deployment config
└── .env.example
```

---

## Running Locally

**1. Clone and install:**
```bash
git clone https://github.com/sujith-raaj/Inteliprompt.git
cd Inteliprompt
pip install -r requirements.txt
```

**2. Set up environment:**
```bash
cp .env.example .env
# Edit .env — add your SECRET_KEY and OPENROUTER_API_KEY
```

**3. Start the backend:**
```bash
uvicorn backend.main:app --reload
# API docs available at http://localhost:8000/docs
```

**4. Start the frontend (new terminal):**
```bash
cd frontend
streamlit run app.py
# App available at http://localhost:8501
```

---

## Deployment

- **Backend:** [Render](https://render.com) free tier — auto-deploys on every GitHub push
- **Frontend:** [Streamlit Community Cloud](https://share.streamlit.io) — free, always on

---

## Key Features

- No login required — open and use instantly
- Session-based history — tracks your prompts per browser session
- 4 LLM adapters — Claude, ChatGPT, Gemini, DeepSeek
- 100% rule-based optimization — no API cost for AMPOA/MAPT
- Quality scoring with detailed dimension breakdown
- Clean chat interface with copyable optimized prompts

---

## Scope

**In Scope:**
- Prompt optimization and translation
- Intent and domain detection
- Prompt quality scoring
- Session-based prompt history
- Multi-LLM support

**Out of Scope:**
- Training or fine-tuning LLMs
- Internet search integration
- Voice assistants
- Document retrieval (RAG)
- User authentication

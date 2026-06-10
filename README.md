# Capital Compass AI — Autonomous Portfolio Intelligence

A multi-agent AI financial portfolio system built with LangGraph, Flask, and Ollama.
Analyses an investor's profile and generates a risk score, asset allocation,
Monte Carlo stress test, compliance review, and plain-language explanation.
Portfolios are auto-rebalanced every 30 days via APScheduler.

---

## Architecture

```
profile → tool_agent → strategy → live_data → simulation → compliance → critic → explanation
```

Each agent writes results into a shared LangGraph state. Downstream agents
skip their work automatically if `tool_calling_agent` already populated the
relevant state keys — preventing duplicate LLM calls and yfinance fetches.

---

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed and running locally

### Pull required Ollama models

```bash
ollama pull phi3:mini
ollama pull nomic-embed-text
```

---

## Setup

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd paradise
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set a strong `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output as the value of `SECRET_KEY` in your `.env` file:

```
SECRET_KEY=your-generated-key-here
FLASK_DEBUG=0
```

### 5. Run the app

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

> **Note:** On first run, the compliance RAG vectorstore will be built and
> persisted to `backend/rag/vectorstore/chroma_compliance_db/`. Subsequent
> starts load it from disk instantly — no re-embedding.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register a new user |
| POST | `/api/login` | Log in |
| POST | `/api/logout` | Log out |
| GET  | `/api/login-check` | Check session status |
| POST | `/api/generate` | Generate portfolio (standard) |
| POST | `/api/generate/stream` | Generate portfolio with SSE real-time progress |
| GET  | `/api/history` | Get portfolio history for logged-in user |
| DELETE | `/api/history/<id>` | Delete a portfolio record |

### `/api/generate` — request body

```json
{
  "age": 30,
  "income": 800000,
  "years": 10,
  "loss": 6,
  "amount": 500000
}
```

| Field | Type | Description |
|-------|------|-------------|
| `age` | int | Investor age (18–100) |
| `income` | float | Annual income in rupees |
| `years` | int | Investment horizon in years (1–50) |
| `loss` | int | Risk tolerance (1 = very low, 10 = very high) |
| `amount` | float | Total investment amount in rupees |

---

## Project Structure

```
paradise/
├── app.py                          # Flask app, routes, SSE streaming, scheduler
├── .env                            # Environment variables (never commit this)
├── .env.example                    # Template for .env
├── requirements.txt
├── README.md
└── backend/
    ├── graph.py                    # LangGraph pipeline definition
    ├── state.py                    # AgentState TypedDict
    ├── llm.py                      # Ollama LLM instance (with timeout)
    ├── tools.py                    # compute_allocation helper
    ├── tool_definitions.py         # LangChain @tool definitions (5 tools)
    ├── risk_engine.py              # calculate_risk_score
    ├── agents/
    │   ├── profile_agent.py        # Calculates risk score
    │   ├── tool_calling_agent.py   # LLM-driven autonomous tool calling
    │   ├── strategy_agent.py       # Generates asset allocation
    │   ├── live_data_agent.py      # Fetches live NIFTY 50 data
    │   ├── simulation_agent.py     # Monte Carlo simulation (1000 runs)
    │   ├── compliance_agent.py     # RAG-based regulatory validation
    │   ├── critic_agent.py         # Reviews and adjusts allocation
    │   └── explanation_agent.py    # Generates plain-language summary
    ├── rag/
    │   └── compliance_rag.py       # Chroma vectorstore (persisted on disk)
    └── compliance_docs/
        └── investment_guidelines.txt
frontend/
    ├── index.html                  # Landing page
    ├── login.html                  # Login page
    ├── register.html               # Registration page
    ├── dashboard.html              # Main dashboard (generate, history, automation)
    └── static/
        └── finlogo.jpeg
```

---

## Key Features

- **7-agent LangGraph pipeline** — profile → tool_agent → strategy → live_data → simulation → compliance → critic → explanation
- **Real-time SSE progress** — live agent-by-agent updates streamed to the dashboard while the pipeline runs
- **PDF export** — downloads a full portfolio report using pure jsPDF
- **Monte Carlo simulation** — 1000 iterations using live NIFTY 50 data or historical CSV fallback
- **RAG compliance validation** — ChromaDB retrieves regulatory guidelines for LLM-based compliance check
- **Auto-rebalancing** — APScheduler re-runs the full pipeline for all users every 30 days
- **Rate limiting** — 10/min on login, 5/min on register (flask-limiter)
- **Auth guard** — all pages check session via `/api/login-check` before rendering

---

## Performance Notes

- CSV data loaded once at module import (not per request)
- RAG vectorstore loaded from disk on startup (not rebuilt each time)
- Downstream agents skip work if `tool_calling_agent` already populated state
- Ollama LLM configured with 120s timeout and 512 token cap
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
- Ollama installed and running locally

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
source venv/bin/activate
venv\Scripts\activate
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

Example:

```
SECRET_KEY=your-generated-key-here
FLASK_DEBUG=0
```

### 5. Run the app

```bash
python app.py
```

Open:

```
http://localhost:5000
```

---

## API Endpoints

| Method | Endpoint | Description |
|----------|----------|----------|
| POST | `/api/register` | Register a new user |
| POST | `/api/login` | Log in |
| POST | `/api/logout` | Log out |
| GET | `/api/login-check` | Check session status |
| POST | `/api/generate` | Generate portfolio |
| POST | `/api/generate/stream` | Generate portfolio with SSE progress |
| GET | `/api/history` | Get portfolio history |
| DELETE | `/api/history/<id>` | Delete portfolio record |

### Sample Request

```json
{
  "age": 30,
  "income": 800000,
  "years": 10,
  "loss": 6,
  "amount": 500000
}
```

---

## Project Structure

```
paradise/
├── app.py
├── .env
├── .env.example
├── requirements.txt
├── README.md
├── backend/
│   ├── graph.py
│   ├── state.py
│   ├── llm.py
│   ├── tools.py
│   ├── tool_definitions.py
│   ├── risk_engine.py
│   ├── agents/
│   ├── rag/
│   └── compliance_docs/
└── frontend/
    ├── index.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    └── static/
```

---

## Key Features

- 7-agent LangGraph pipeline
- Autonomous tool calling
- Real-time SSE progress updates
- PDF report export
- Monte Carlo portfolio simulation
- RAG-based compliance validation
- Automated portfolio rebalancing
- Session-based authentication
- Rate limiting and security controls

---

## Performance Notes

- CSV data loaded once at startup
- RAG vectorstore persisted on disk
- Duplicate agent work avoided through shared state
- Ollama configured with timeout protection
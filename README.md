````markdown
# Capital Compass AI — Autonomous Portfolio Intelligence

Capital Compass AI is a multi-agent financial portfolio intelligence system
built using **Python, Flask, LangGraph, OpenAI GPT-4o-mini, RAG, Yahoo Finance,
and Monte Carlo simulation**.

The system analyzes an investor's financial profile and generates a complete
portfolio analysis including risk assessment, asset allocation, market data,
Monte Carlo stress testing, compliance validation, and a plain-language
explanation.

---

## Architecture

```text
Profile Agent
      ↓
Tool Calling Agent
      ↓
Strategy Agent
      ↓
Live Data Agent
      ↓
Simulation Agent
      ↓
Compliance Agent
      ↓
Critic Agent
      ↓
Explanation Agent
````

All agents operate on a shared LangGraph state.

Agents check whether required results are already available before performing
their work, helping reduce duplicate processing and unnecessary model or
data calls.

---

## Key Features

### 🤖 Multi-Agent AI System

Built with LangGraph and specialized agents for different stages of portfolio
analysis.

### 🧠 OpenAI GPT-4o-mini

OpenAI GPT-4o-mini powers the LLM-based reasoning, autonomous tool calling,
compliance analysis, and portfolio explanation.

### 🔧 Autonomous Tool Calling

The Tool Calling Agent can select and execute financial analysis tools such
as:

* Risk score calculation
* Asset allocation
* NIFTY 50 market data
* Monte Carlo simulation
* Compliance checking

### 📊 Risk Analysis

Calculates an investor risk score using:

* Age
* Income
* Investment horizon
* Loss tolerance

### 💰 Portfolio Allocation

Generates a recommended allocation across:

* Stocks
* Bonds
* Cash

### 📈 Live NIFTY 50 Data

Retrieves NIFTY 50 market data using Yahoo Finance.

If live market data is unavailable, the system can use historical market
data for simulation.

### 🎲 Monte Carlo Simulation

Runs **1,000 simulations** to estimate portfolio outcomes.

The system calculates:

* Expected Portfolio Value
* Worst 5% Case
* Best 5% Case

### 📚 RAG-Based Compliance

Uses Retrieval-Augmented Generation to retrieve relevant compliance
information before performing portfolio validation.

### 🔍 Critic Agent

Reviews the generated portfolio and can route the workflow back to the
Strategy Agent when another iteration is required.

### 💬 AI Explanation

Converts the technical portfolio analysis into a concise,
plain-language explanation.

### 📡 Real-Time Progress

Provides an SSE-based streaming endpoint to display agent execution
progress in real time.

### 🔐 Authentication

Includes:

* User registration
* Login
* Logout
* Session authentication
* Password hashing

### 🛡️ Security

Includes:

* API rate limiting
* Input validation
* Environment-based secrets
* Protected API endpoints

### 🔄 Automated Rebalancing

Uses APScheduler to periodically re-run portfolio analysis for existing
users.

### 📜 Portfolio History

Users can:

* Generate portfolios
* View previous portfolios
* Delete portfolio records

---

## Technology Stack

### Backend

* Python
* Flask
* LangGraph
* LangChain
* SQLite
* APScheduler

### AI

* OpenAI GPT-4o-mini
* LangChain ChatOpenAI
* LangGraph
* Retrieval-Augmented Generation (RAG)

### Financial Data

* Yahoo Finance
* yfinance
* Historical CSV datasets

### Data Science

* NumPy
* Pandas
* Monte Carlo Simulation

### Frontend

* HTML
* CSS
* JavaScript

### Deployment

* Vercel

---

## Project Structure

```text
capital-compass-ai/
│
├── app.py
├── README.md
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
│
├── backend/
│   ├── graph.py
│   ├── state.py
│   ├── llm.py
│   ├── tools.py
│   ├── tool_definitions.py
│   ├── risk_engine.py
│   │
│   ├── agents/
│   │   ├── profile_agent.py
│   │   ├── tool_calling_agent.py
│   │   ├── strategy_agent.py
│   │   ├── live_data_agent.py
│   │   ├── simulation_agent.py
│   │   ├── compliance_agent.py
│   │   ├── critic_agent.py
│   │   └── explanation_agent.py
│   │
│   ├── rag/
│   │   └── compliance_rag.py
│   │
│   ├── compliance_docs/
│   │
│   └── data/
│       ├── nifty_annual_returns.csv
│       └── bond_annual_returns.csv
│
└── frontend/
    ├── index.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    └── static/
```

---

## Prerequisites

* Python 3.11+
* Git
* OpenAI API access

---

## Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd capital-compass-ai
```

### 2. Create a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file:

```env
OPENAI_API_KEY=your-openai-api-key
SECRET_KEY=your-secret-key
FLASK_DEBUG=0
```

Generate a secure Flask secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Security

Never commit `.env` or API keys to GitHub.

Add the following to `.gitignore`:

```text
.env
venv/
__pycache__/
*.pyc
```

---

## Running the Application

Start the Flask application:

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

---

## API Endpoints

| Method | Endpoint               | Description                          |
| ------ | ---------------------- | ------------------------------------ |
| POST   | `/api/register`        | Register a new user                  |
| POST   | `/api/login`           | Log in                               |
| POST   | `/api/logout`          | Log out                              |
| GET    | `/api/login-check`     | Check session status                 |
| POST   | `/api/generate`        | Generate portfolio analysis          |
| POST   | `/api/generate/stream` | Generate portfolio with SSE progress |
| GET    | `/api/history`         | Retrieve portfolio history           |
| DELETE | `/api/history/<id>`    | Delete portfolio record              |

---

## Sample Request

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

## Portfolio Generation Flow

```text
Investor Profile
       ↓
Risk Score
       ↓
Autonomous Tool Calling
       ↓
Asset Allocation
       ↓
NIFTY 50 Market Data
       ↓
Monte Carlo Simulation
       ↓
Compliance Validation
       ↓
Critic Review
       ↓
AI Explanation
       ↓
Final Portfolio Analysis
```

---

## AI and Fallback Architecture

The application uses OpenAI GPT-4o-mini for LLM-powered functionality.

The core financial calculations are handled independently through
deterministic tools and simulation logic.

This separation allows components such as:

* Risk calculation
* Asset allocation
* Monte Carlo simulation
* Historical market-data analysis

to operate independently of generative AI.

When supported, fallback logic can be used when external services are
temporarily unavailable.

---

## Performance Optimizations

Capital Compass AI includes several optimizations:

* Shared LangGraph state
* Duplicate agent-work prevention
* Cached historical datasets
* Lazy RAG initialization
* Live market-data fallback
* SSE streaming
* Background portfolio rebalancing

---

## Cloud Deployment

The application can be deployed to a cloud platform such as Vercel.

Configure the following environment variables in the deployment platform:

```text
OPENAI_API_KEY
SECRET_KEY
FLASK_DEBUG
```

The OpenAI API key must remain server-side and must never be exposed in
frontend JavaScript.

### Deployment Architecture

```text
Browser
   ↓
Vercel
   ↓
Flask Backend
   ↓
LangGraph
   ↓
OpenAI GPT-4o-mini
   ↓
Financial Analysis Tools
   ↓
Final Portfolio
```

---

## Limitations

* OpenAI API access is required for LLM-powered features.
* API usage is subject to OpenAI account limits and pricing.
* Live market data depends on Yahoo Finance availability.
* SQLite is primarily suitable for development and demonstration workloads.
* Cloud/serverless environments may have execution and storage limitations.
* Financial simulations are estimates and are not guaranteed future results.

---

## Disclaimer

Capital Compass AI is an educational and software engineering project.

The portfolio allocations, financial simulations, compliance results, and
AI-generated explanations are not professional financial advice.

Users should consult a qualified financial professional before making actual
investment decisions.


# 🤖 AgenticSQL — AI-Powered Autonomous Data Analyst

> **Production-Grade Agentic Data Analyst with Self-Correcting Text-to-SQL & Dynamic Dataset Ingestion**
>
> Ask questions about your business data in natural language. Get optimized SQL, interactive Plotly visualizations, statistical summaries, and plain-English explanations — automatically.

---

## 📸 Application Showcase

### 🖥️ Main Analytics Dashboard
![AgenticSQL Main Interface](screenshots/interface.jpeg)

---

### 📊 Query Execution, Auto-Visualization & Insights
*Analyzing an uploaded LeetCode dataset (1,825 rows) in natural language:*

![Query Execution and Chart](screenshots/leetcodedatasetqueryexecuted1.jpeg)

---

### 📈 Interactive Plotly Visualization & Metrics
*Dynamic chart generation and automated data insights:*

![Visualization and Insights](screenshots/leetcodedatasetqueryexecuted2.jpeg)

---

### 🔍 Transparent Query Details & Data Preview
*View generated SQL, plain-English explanation, and interactive tabular data:*

![Query Details and Data Table](screenshots/leetcodedatasetqueryexecuted3.jpeg)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Agent Workflow (LangGraph)](#-agent-workflow-langgraph)
- [Datasets Supported](#-datasets-supported)
- [Tech Stack](#-tech-stack)
- [Quick Start with Docker](#-quick-start-with-docker)
- [Local Development Setup](#-local-development-setup)
- [Configuration (.env)](#-configuration-env)
- [Self-Correction Mechanism](#-self-correction-mechanism)
- [Evaluation & Benchmarking](#-evaluation--benchmarking)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [License](#-license)

---

## 🎯 Overview

**AgenticSQL** is an autonomous AI data analyst that bridges the gap between raw data and business intelligence. Unlike simple "Prompt → SQL" wrappers, AgenticSQL executes a **complete agentic state machine**:

1. **Intelligent Query Planning:** Dynamically introspects database schemas and selects the exact tables needed.
2. **Universal Dataset Support:** Query the built-in enterprise PostgreSQL database OR drop in any custom CSV file for instant in-memory analysis.
3. **Safety & Validation Gateways:** Strictly enforces read-only query execution, blocking any destructive operations (`INSERT`, `DROP`, `DELETE`, etc.).
4. **Self-Correcting Execution Loop:** Automatically catches SQL syntax or execution errors, passes the traceback to an error analyzer, and self-corrects the query with up to 3 automated retry attempts.
5. **Auto-Visualization & Business Insights:** Inspects query results, selects the optimal chart type (bar, line, scatter, pie), and writes bulleted executive insights.
6. **Full Transparency:** Every query exposes generated SQL, plain-English explanations, execution times, retry counts, and paginated data previews.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🧠 **Natural Language to SQL** | Ask questions in plain English; get clean, optimized SQL queries. |
| 📁 **Instant CSV Ingestion** | Drag and drop any CSV (up to 200MB) for automatic in-memory SQLite ingestion and immediate querying. |
| 🔄 **Self-Correcting Loop** | Detects execution errors and autonomously self-heals queries (up to 3 retries). |
| 🛡️ **Multi-Tier Safety Guard** | SQL AST validation blocks destructive statements (`DROP`, `ALTER`, `TRUNCATE`, multi-statement injections). |
| 📊 **Dynamic Plotly Charts** | Generates responsive, interactive data visualizations matched to the analytical dimension. |
| 💡 **Automated Data Insights** | Synthesizes complex aggregations into actionable business bullet points. |
| 📖 **Plain-English Explanations** | Explains query logic, joins, aggregations, and filters for non-technical stakeholders. |
| 📜 **Query History & Sessions** | Tracks previous questions and answers with instant recall and session isolation. |
| ⚡ **Multi-Provider LLM Engine** | Supports Groq, OpenAI, Google Gemini, and Anthropic Claude. |
| 🐳 **Dockerized One-Click Launch** | Fully containerized with live volume mounts for immediate development and deployment. |

---

## 🏗 Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Streamlit Frontend                   │
│         (Chat Interface, File Upload, Plotly)          │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP REST API
┌───────────────────────────▼────────────────────────────┐
│                    FastAPI Backend                     │
│               (Session Mgmt & Endpoints)               │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│             LangGraph Agent State Machine              │
│  [Planner] ➔ [Generator] ➔ [Validator] ➔ [Executor]    │
│                     ↺ [Self-Correction Loop]          │
│              [Analyzer] ➔ [Visualizer] ➔ [Builder]     │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
┌──────────────▼─────────────┐ ┌──────────▼──────────────┐
│     PostgreSQL Database    │ │    In-Memory SQLite     │
│   (Pre-Seeded Enterprise)  │ │   (Uploaded CSV Data)   │
└────────────────────────────┘ └─────────────────────────┘
```

---

## 🔄 Agent Workflow (LangGraph)

The core analytical pipeline is orchestrated as a state graph:

```mermaid
flowchart TD
    START([User Question]) --> Planner[Query Planner & Schema Introspection]
    Planner -->|Is Data Question?| SQLGen[SQL Generator]
    Planner -->|Out of Scope| OutOfScope[Response Builder]
    
    SQLGen --> SQLVal{SQL Safety Validator}
    SQLVal -->|Passed| SQLExec[SQL Executor]
    SQLVal -->|Blocked/Unsafe| Failed[Response Builder]
    
    SQLExec -->|Execution Success| DataAnalyzer[Data Analyzer]
    SQLExec -->|SQL Error| ErrorCheck{Retries < 3?}
    
    ErrorCheck -->|Yes| ErrorAnalyzer[Error Analyzer]
    ErrorAnalyzer --> SQLCorrector[SQL Corrector]
    SQLCorrector --> SQLVal
    
    ErrorCheck -->|No| MaxRetriesExceeded[Response Builder]
    
    DataAnalyzer --> Visualizer[Plotly Visualizer]
    Visualizer --> ResponseBuilder[Response Builder]
    ResponseBuilder --> END([Final Answer + Chart + Insights])
    OutOfScope --> END
    Failed --> END
    MaxRetriesExceeded --> END
```

---

## 💾 Datasets Supported

### 1. Uploaded Custom Datasets (CSV)
Drag and drop any custom CSV dataset in the sidebar. AgenticSQL automatically parses the file, normalizes column names, loads it into an ephemeral session database, and inspects its schema.
* *Example shown above:* **LeetCode Problems Dataset** (`1,825 rows, 19 columns`)
* Supports medical, scientific, financial, operational, and custom tabular datasets.

### 2. Pre-Seeded Enterprise PostgreSQL Database
A pre-seeded e-commerce analytics database configured with:
* **`customers`** (~1,000 customers with location and registration metadata)
* **`products`** (~100 products across 8 categories with cost and retail prices)
* **`orders`** (~5,000 orders spanning 2024–2025)
* **`order_items`** (~10,000+ line items with pricing and quantities)
* **`payments`** (~5,000 transactions across multiple payment methods)

---

## 🛠 Tech Stack

* **Frontend:** [Streamlit](https://streamlit.io/), [Plotly](https://plotly.com/python/)
* **Backend:** [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
* **Agentic Framework:** [LangGraph](https://langchain-ai.github.io/langgraph/), [LangChain](https://www.langchain.com/)
* **Database & ORM:** [PostgreSQL 16](https://www.postgresql.org/), [SQLite](https://www.sqlite.org/), [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
* **Data Processing:** [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
* **SQL Parsing & Validation:** [sqlparse](https://sqlparse.readthedocs.io/)
* **Supported LLMs:** Groq (`openai/gpt-oss-120b`, `llama-3.1-8b-instant`), Google Gemini (`gemini-2.5-flash`), OpenAI (`gpt-4o`), Anthropic Claude

---

## 🚀 Quick Start with Docker

The fastest way to launch the complete system (PostgreSQL, FastAPI Backend, and Streamlit Frontend):

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/AgenticSQL.git
cd AgenticSQL
```

### 2. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` and set your preferred LLM provider and API key (e.g. Groq):
```dotenv
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
LLM_API_KEY=gsk_your_groq_api_key_here
```

### 3. Start services with Docker Compose
```bash
docker compose up --build
```

### 4. Access the web interface
Open your browser at **[http://localhost:8501](http://localhost:8501)**.

---

## 💻 Local Development Setup

If you prefer to run services individually without containerizing the app:

### 1. Launch PostgreSQL Database
```bash
docker compose up postgres
```

### 2. Start the FastAPI Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start the Streamlit Frontend
```bash
# In a new terminal window:
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

---

## ⚙️ Configuration (.env)

| Variable | Description | Example / Default |
|---|---|---|
| `LLM_PROVIDER` | LLM service provider (`groq`, `google_genai`, `openai`, `anthropic`) | `groq` |
| `LLM_MODEL` | Model identifier | `openai/gpt-oss-120b` |
| `LLM_API_KEY` | Provider API key | `gsk_...` or `AIza...` |
| `LLM_TEMPERATURE` | Generation temperature | `0.0` |
| `DATABASE_URL` | PostgreSQL admin connection string | `postgresql+psycopg2://postgres:postgres@localhost:5432/agenticsql` |
| `DATABASE_URL_READONLY` | Read-only connection string | `postgresql+psycopg2://postgres:postgres@localhost:5432/agenticsql` |
| `MAX_RETRY_COUNT` | Max SQL correction retries | `3` |
| `MAX_RESULT_ROWS` | Result safety row limit | `1000` |
| `QUERY_TIMEOUT_SECONDS` | Query timeout threshold | `30` |

---

## 🔄 Self-Correction Mechanism

When an executed query throws a database error, AgenticSQL executes a recovery routine rather than failing:

```
User Query: "Show average acceptance rate by difficulty"

Attempt 1:
  Generated SQL: SELECT difficulty, AVG(rate) FROM leetcode_dataset GROUP BY difficulty;
  Database Error: column "rate" does not exist

  ➔ Error Analyzer: Column "rate" is missing. Available columns: [acceptance_rate, ...].
  ➔ SQL Corrector: Replaces "rate" with "acceptance_rate".

Attempt 2:
  Corrected SQL: SELECT difficulty, AVG(acceptance_rate) AS avg_acceptance
                 FROM leetcode_dataset GROUP BY difficulty;
  ✅ Execution Succeeded!

Status: Auto-Corrected (1 Retry)
```

---

## 📈 Evaluation & Benchmarking

The built-in evaluation suite benchmark includes **65 real-world queries** across:
* Simple Aggregations & Grouping
* Multi-table Joins & Subqueries
* Date/Time Window Calculations
* Out-of-Scope Prompt Rejection

To run the evaluation:
```bash
cd backend
python -m evaluation.evaluate
```

---

## 🧪 Testing

Comprehensive test suites covering SQL safety, conversation memory, visualization formatting, and graph nodes:

```bash
cd backend

# Run all unit tests
pytest tests/ -v

# Run with test coverage
pytest tests/ --cov=app --cov-report=term-missing
```

---

## ☁️ Deployment

* **Frontend:** Ready for one-click deployment to [Streamlit Community Cloud](https://share.streamlit.io/).
* **Backend:** Deployable to [Render](https://render.com/), [Railway](https://railway.app/), or [Fly.io](https://fly.io/) via the provided `backend/Dockerfile`.

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

*Built with ❤️ using LangGraph, LangChain, FastAPI, Streamlit, PostgreSQL, and Plotly.*

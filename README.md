# High-Performance Call Center Analytics Pipeline

A scalable, asynchronous data ingestion and monitoring system built with **FastAPI**, **RabbitMQ**, and **MySQL**. This project demonstrates two architectural patterns: Direct Database Persistence and Message-Queue based Batch Processing.

## 🚀 System Architecture


The system is split into three main components:
1. **API-1 (Ingestion & Validation):** Validates incoming JSON call payloads using Pydantic and forwards them to the storage layer.
2. **API-2 / API-2 MQ (Storage Layer):** - `api_2.py`: Direct insertion into MySQL.
   - `api_2_mq.py`: Publishes messages to RabbitMQ for high-throughput scenarios.
3. **Worker (Background Processor):** Consumes messages from RabbitMQ and performs **Batch Inserts** (500 records or every 2 seconds) to optimize DB performance.
4. **API-3 (Monitoring):** Provides analytical summaries, filtering by campaign, status, and performance metrics.

## 🛠️ Tech Stack
- **Framework:** FastAPI (Asynchronous)
- **Database:** MySQL (via `aiomysql`)
- **Messaging:** RabbitMQ (via `aio-pika`)
- **ORM/Validation:** SQLAlchemy & Pydantic v2
- **Load Testing:** Locust

## 📈 Performance
- **Concurrency:** Designed to handle high-concurrency requests.
- **Observed Throughput:** Achieved ~400 Requests Per Second (RPS) during local stress testing (limited by hardware).
- **Optimization:** Uses connection pooling and batch processing to minimize DB overhead.

## 📋 Prerequisites
- Python 3.10+
- MySQL Server
- RabbitMQ Server

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/your-repo-name.git](https://github.com/yourusername/your-repo-name.git)
   cd your-repo-name
2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
3. **Database Setup:** Create a database named call_center_db and a table call_records based on the schema in models.py.
4. **Running the Services:**
  - Option A: Direct Storage (Standard)
    ```bash
    uvicorn api_1:app --port 8000 --reload
    uvicorn api_2:app --port 8001 --reload
  - Option B: Scalable Queue Storage (Recommended)
    ```bash
    # Start the services
    uvicorn api_1:app --port 8000 --reload
    uvicorn api-2_mq:app --port 8001 --reload
    # Start the background worker
    python worker.py
5. **Monitoring:**
    ```bash
    uvicorn api_3:app --port 8002 --reload
- 🧪 Load Testing
To run the performance tests:
    ```bash
    locust -f locustfile.py --host http://localhost:8000
Visit *http://localhost:8089* to configure the number of users and spawn rate.


# 🤖 Call Center Data Analyst (ReAct Agent)

This LangGraph agent uses Google Gemini 2.0 Flash to provide a natural language interface for call center analytics. It interacts with API-3 (Monitoring API) to retrieve and synthesize data insights.

> [!IMPORTANT]
> The ReAct agent implementation and logic are located within the Agent folder.

## 🌟 Key Features
- ReAct Architecture: Implements a Reasoning and Acting loop to manage tool execution and data summarization.
- Parameter Mapping: Automatically maps natural language entities (campaigns, dates, status) into API query parameters.
- Persistence: Built-in `SqliteSaver` allows the agent to remember conversation context.

## 🛠️ Tech Stack
- LLM: Google Gemini 2.0 Flash
- Framework: [LangGraph](https://langchain-ai.github.io)
- Networking: `httpx` (Asynchronous)
- Persistence: `langgraph-checkpoint-sqlite`

## 🚀 Quick Start
1. Install: `pip install langchain-google-genai langgraph-checkpoint-sqlite`
2. Configure: Add `GEMINI_API_KEY` to your secrets and update the `Base URL` in the prompt to your API-3 tunnel address.
3. Run: Use the `graph.stream()` loop to interact with the analyst.

## 📊 Example
**User:** "How many calls did we miss in the Sales campaign?"
**Agent:** (Reasoning → Tool Call → Observation) "There were 12 missed calls for the Sales campaign according to the latest records."


## 📝 API Endpoints
- POST `/api/receive` : Main entry point for call data.

- GET `/api/monitor/summary` : Get breakdown of calls by campaign, status, and average processing times.

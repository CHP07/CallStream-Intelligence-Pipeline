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
    uvicorn api_1:app --port 8000
    uvicorn api_2:app --port 8001
  - Option B: Scalable Queue Storage (Recommended)
    ```bash
    # Start the services
    uvicorn api_1:app --port 8000
    uvicorn api_2_mq:app --port 8001
    # Start the background worker
    python worker.py
5. **Monitoring:**
    ```bash
    uvicorn api_3:app --port 8002
- 🧪 Load Testing
To run the performance tests:
    ```bash
    locust -f locustfile.py --host http://localhost:8000
Visit *http://localhost:8089* to configure the number of users and spawn rate.

## 📝 API Endpoints
- POST `/api/receive` : Main entry point for call data.

- GET `/api/monitor/summary` : Get breakdown of calls by campaign, status, and average processing times.

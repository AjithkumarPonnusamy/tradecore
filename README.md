# TradeCore

TradeCore is a full-stack trading platform for market analysis, trade journaling, scanner automation, AI-assisted research, and dashboard-based workflow management. The project combines a FastAPI backend, a Next.js frontend, and supporting services for PostgreSQL, Redis, Ollama, and AI workflows.

## Overview

TradeCore is designed to help traders manage:

- trade execution and trade records
- market data monitoring and screening
- checklist and workflow tracking
- backtesting and scanner configurations
- voice journaling and AI-assisted research
- dashboard views for portfolio, market, and system insights

The system is organized into multiple domains and includes background automation for scheduled scanning tasks.

## Tech stack

- Backend: Python, FastAPI
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Database: PostgreSQL
- Cache/Queue: Redis
- AI: Ollama + local inference services
- Containerization: Docker + Docker Compose

## Repository structure

```text
tradecore/
├── ai_service/
│   ├── app/
│   ├── Dockerfile
│   └── ...
├── backend/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── README.md
├── docker/
│   └── historical-market-db/
├── docs/
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── Dockerfile
│   └── README.md
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Core components

### Backend

The backend is a FastAPI application located in `backend/app` and exposes API routes grouped by domain:

- auth
- trades
- dashboard
- screener
- checklists
- market
- scanners
- backtesting
- journal
- voice_journal
- research
- system

The app startup also initializes the database and starts a background scanner thread that periodically checks scanner settings and runs automated scans.

### Frontend

The frontend is a Next.js application under `frontend/` and is configured to communicate with the backend at:

- `http://localhost:8000/api/v1`

It provides the user interface for trading workflow and data visualization.

### AI services

The project contains an AI microservice under `ai_service/` and uses Ollama for local LLM inference. This supports features like:

- voice transcription workflows
- trade extraction
- emotion analysis
- summary generation
- research assistance

### Data layer

PostgreSQL is used for structured app data, and Redis is used for caching and task orchestration. A separate TimescaleDB-based historical market DB is also configured under `docker/historical-market-db/`.

## Services in Docker Compose

The root `docker-compose.yml` defines these services:

- `postgres` — application database
- `redis` — message/cache layer
- `backend` — FastAPI backend service
- `celery_worker` — background task worker
- `ai-service` — AI service API
- `ai-worker` — AI task worker
- `ollama` — local LLM runtime
- `ollama-setup` — model pull bootstrap
- `frontend` — Next.js UI

## Prerequisites

Before running the project locally, install:

- Docker and Docker Compose
- Git
- Node.js (for frontend development)
- Python 3.11+ (for backend development)

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/AjithkumarPonnusamy/tradecore.git
cd tradecore
```

### 2. Start the stack

```bash
docker compose up --build
```

This will start the PostgreSQL, Redis, backend, frontend, AI service, and Ollama-based services.

### 3. Access the app

- Frontend: http://localhost:3005
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- AI Service: http://localhost:8001
- Ollama: http://localhost:11434

## Environment configuration

The backend service depends on environment variables loaded from `backend/.env` and runtime variables declared in `docker-compose.yml`.

Example configuration pattern:

```env
DATABASE_URL=postgresql://postgres:ak@postgres:5432/tradecore
JWT_SECRET_KEY=super_secret_key_change_me_in_production_1234567890
REDIS_URL=redis://redis:6379/0
LLM_API_BASE=http://ollama:11434/v1
LLM_MODEL=llama3.2:1b
WHISPER_MODEL=large-v3
WHISPER_DEVICE=cpu
AI_SERVICE_URL=http://ai-service:8001
```

## Development workflow

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Important notes

- This project includes live service integrations and local AI model execution.
- Some components are configured for local development and may need tuning for production deployment.
- Secret keys and environment settings should be reviewed before production use.

## Roadmap / possible extensions

The codebase already suggests a broad trading platform with domain modules. Common next improvements include:

- production-grade auth and RBAC
- secure secrets management
- deployment hardening for Docker and Kubernetes
- real market data integrations
- strategy backtesting dashboards
- analytics pipelines for trade performance
- observability and monitoring

## License

No explicit license is set in the repository currently.

## Status

This repository is active and structured as a multi-service trading system with backend, frontend, AI, database, and automation layers.

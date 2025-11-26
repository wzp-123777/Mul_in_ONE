# Mul-in-One Project Context

## Project Overview

**Mul-in-One** is an advanced multi-agent conversational system built on the NVIDIA NeMo Agent Toolkit. The project enables natural group chat interactions between multiple AI agents (Personas), each with unique personalities, knowledge bases, and API configurations. It features full RAG (Retrieval-Augmented Generation) integration, allowing Personas to leverage external knowledge for contextually rich responses.

### Key Capabilities

- **Dynamic Multi-Agent Scheduling**: Agents decide when to speak based on proactivity, cooldown mechanisms, and conversation context
- **RAG Knowledge Enhancement**: Complete vector-based retrieval system using Milvus for persona-specific knowledge injection
- **Database-Driven Configuration**: Runtime resolution of LLM API configs per Persona, supporting multi-tenant SaaS architecture
- **Dual Interface**: Web-based UI (Vue.js) and CLI for flexible interaction modes
- **Real-time Streaming**: WebSocket-based message streaming with SSE-style events
- **Unlimited Session Context**: Support for unlimited history window and turn-based agent participation

## Technology Stack

### Backend
- **Python 3.13**, FastAPI, SQLAlchemy (async)
- **NVIDIA NeMo Agent Toolkit** (conversation orchestration)
- **LangChain** (RAG chain: OpenAIEmbeddings, OpenAI LLM)
- **Milvus** (vector database for retrieval)
- **PostgreSQL** (relational data), Alembic (migrations)
- **Package Manager**: `uv`

### Frontend
- **Vue.js 3**, Quasar (UI components)
- **Vite** (build tool), **npm**

### Infrastructure
- **Docker** (Milvus deployment)
- **Nix** (optional dev environment)

## Architecture Overview

```
┌─────────────┐
│   Frontend  │  Vue.js + Quasar + WebSocket
└──────┬──────┘
       │ HTTP/WS
┌──────▼──────────────────────────────────────┐
│         FastAPI Backend                     │
│  ┌──────────────────────────────────────┐  │
│  │  Routers (Sessions, Personas, RAG)   │  │
│  └─────────┬────────────────────────────┘  │
│  ┌─────────▼────────────────────────────┐  │
│  │  Services (SessionService, RAG)      │  │
│  └─────────┬────────────────────────────┘  │
│  ┌─────────▼────────────────────────────┐  │
│  │  Repositories (DB access layer)      │  │
│  └─────────┬────────────────────────────┘  │
└────────────┼────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼─────┐
│ Postgres│      │  Milvus  │
│  (SQL) │      │ (Vector) │
└────────┘      └──────────┘
             │
    ┌────────┴────────────┐
    │                     │
┌───▼──────────┐   ┌─────▼────────┐
│ NeMo Runtime │   │  LLM APIs    │
│  (Scheduler) │   │  (OpenAI)    │
└──────────────┘   └──────────────┘
```

## Project Structure

```
├── src/mul_in_one_nemo/          # Backend Python package
│   ├── service/                  # FastAPI application
│   │   ├── routers/              # API routes (sessions, personas, RAG)
│   │   ├── repositories.py       # Data access layer
│   │   ├── dependencies.py       # Dependency injection
│   │   ├── rag_service.py        # RAG ingestion & retrieval
│   │   └── session_service.py    # Session orchestration
│   ├── db/                       # SQLAlchemy models & config
│   ├── runtime.py                # NeMo Agent integration
│   ├── scheduler.py              # Turn-based agent scheduling
│   ├── memory.py                 # Conversation history
│   ├── persona_function.py       # Persona dialogue logic + RAG injection
│   └── cli.py                    # Command-line interface
├── src/mio_frontend/mio-frontend/  # Vue.js frontend
├── alembic/                      # Database migrations
├── tests/                        # Pytest test suite
├── personas/                     # YAML prototype configs
├── scripts/                      # Utility scripts
└── external/NeMo-Agent-Toolkit/  # Submodule dependency
```

## Quick Start

### Prerequisites
- Python 3.11+, `uv` package manager
- Node.js, npm
- PostgreSQL
- Docker (for Milvus)

### 1. Initial Setup
```bash
# Clone and bootstrap
git clone <repository-url>
cd Mul_in_ONE
uv venv .venv && source .venv/bin/activate
./scripts/bootstrap_toolkit.sh
```

### 2. Start Services
```bash
# PostgreSQL
./scripts/db_start.sh

# Milvus (vector store)
docker run -d --name milvus-standalone \
  -p 19530:19530 -p 9091:9091 \
  -e ETCD_USE_EMBED=true \
  milvusdb/milvus:latest

# Run DB migrations
alembic upgrade head
```

### 3. Backend
```bash
uvicorn mul_in_one_nemo.service.main:app --reload
# API docs: http://127.0.0.1:8000/docs
```

### 4. Frontend
```bash
cd src/mio_frontend/mio-frontend
npm install && npm run dev
# UI: http://localhost:5173
```

### 5. CLI (Optional)
```bash
uv run mul-in-one-nemo --stream
```

## Key Features Implemented

### ✅ RAG Integration (Complete)
- **Ingestion**: `/api/personas/{id}/ingest` (URL), `/ingest_text` (raw text)
- **Vector Storage**: Per-persona Milvus collections
- **Retrieval**: Async document lookup during conversation
- **Generation**: Context-injected LLM responses via LangChain

### ✅ Database Configuration Resolution
- Dynamic API config loading per Persona from `APIProfile` table
- Encrypted API key storage (Fernet)
- Runtime LLM/Embedder instantiation

### ✅ Persona Background Field
- Full backend support (models, repos, routes)
- Frontend UI for editing unlimited-length biography
- **Background text is ingested into RAG** (not used as direct system prompt)
- Workflow: User creates Persona with background → Background auto-ingested as RAG document → Retrieved during conversation

### ✅ Unlimited Session Semantics
- `memory_window = -1`: Full conversation history
- `max_agents_per_turn = -1`: All participants can speak

## Development Conventions

- **Backend**: FastAPI dependency injection, async/await throughout
- **Testing**: `pytest` with async support (`pytest-asyncio`)
- **Database**: SQLAlchemy 2.0+ async session, Alembic for schema changes
- **Frontend**: Vue 3 Composition API, TypeScript interfaces for API contracts
- **Code Style**: Black (formatting), Ruff (linting)

## Testing
```bash
# Run all tests
uv run pytest tests -v

# Run specific module
uv run pytest tests/test_rag_service.py -v
```

## API Highlights

### Sessions
- `POST /api/sessions` - Create session
- `GET /api/sessions/{id}` - Get session details
- `POST /api/sessions/{id}/messages` - Send message
- `WS /api/ws/sessions/{id}` - Stream responses

### Personas
- `GET /api/personas` - List personas
- `POST /api/personas` - Create persona (with background)
- `PATCH /api/personas/{id}` - Update persona
- `POST /api/personas/{id}/ingest` - Ingest knowledge (RAG)

### RAG
- `POST /api/personas/{id}/ingest` - URL ingestion
- `POST /api/personas/{id}/ingest_text` - Text ingestion

## Current Status (2025-11-26)

**Stable & Production-Ready:**
- Multi-agent conversation engine with dynamic scheduling
- Full RAG pipeline (ingest → retrieve → generate)
- Database-backed Persona & API management
- Real-time WebSocket streaming
- 22 passing tests

**Next Roadmap:**
- Frontend RAG management UI
- Retrieval quality improvements (query rewriting, reranking)
- Observability (metrics, tracing)
- Vector store management APIs
*   **Configuration**: The application is configured through environment variables and YAML files in the `personas/` directory. The `.envrc` file is used to manage environment variables for development.

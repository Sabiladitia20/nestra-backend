# Dashboard Nestra — AI/ML Backend

Production-ready FastAPI backend untuk AI/ML/LLM processing pada Dashboard Nestra.

## 📁 Project Structure

```
backend/
├── run.py                  # Entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
├── .env.example            # Environment template
├── .gitignore
│
├── app/
│   ├── __init__.py         # Package metadata
│   ├── main.py             # FastAPI application factory
│   │
│   ├── core/               # Configuration & infrastructure
│   │   ├── config.py       # Pydantic settings
│   │   └── logging.py      # Loguru setup
│   │
│   ├── api/                # API layer
│   │   ├── __init__.py     # Router aggregator
│   │   └── routes/
│   │       ├── chat.py     # POST /api/v1/chat
│   │       └── health.py   # GET  /api/v1/health
│   │
│   ├── schemas/            # Pydantic request/response models
│   │   └── chat.py
│   │
│   ├── services/           # Business logic
│   │   ├── llm_service.py  # OpenAI / LLM integration
│   │   ├── rag_service.py  # RAG pipeline (placeholder)
│   │   └── ml_service.py   # ML models (placeholder)
│   │
│   ├── models/             # Database models (future)
│   └── utils/              # Shared utilities
│
├── tests/                  # Test suite
│   └── test_chat.py
│
├── data/                   # ChromaDB & data storage
└── logs/                   # Application logs
```

## 🚀 Quick Start

### 1. Create Virtual Environment
```bash
cd backend
python -m venv venv
```

### 2. Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 5. Run the Server
```bash
python run.py
```

Server will start at `http://localhost:8000`

### 6. View API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root — app info & links |
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/chat` | Chat with Mahi AI |

### Chat Request Example
```json
{
  "message": "Analisis potensi angin di Pandeglang",
  "conversation_history": [],
  "context": {
    "site": "Pandeglang",
    "page": "wind-prediction"
  }
}
```

## 🧪 Running Tests
```bash
pytest tests/ -v
```

## 🏗️ Architecture

- **Clean Architecture** — separated layers (API → Services → Models)
- **Dependency Injection** — singleton services with factory functions
- **Pydantic Settings** — typed configuration from environment
- **Loguru** — structured logging with rotation
- **CORS** — configured for Next.js frontend
- **Mock Fallback** — works without OpenAI API key in dev mode

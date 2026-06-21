# FastAPI Services

A scalable, production-ready FastAPI server structure for the ShieldX project.

## Project Structure

```
services/
├── app/                      # Main application package
│   ├── api/                  # API endpoints
│   │   └── v1/               # API v1
│   │       └── endpoints/
│   ├── models/               # Data models and schemas
│   ├── services/             # Business logic
│   ├── middleware/           # Custom middleware
│   ├── utils/                # Utility functions
│   ├── config.py             # Configuration management
│   ├── exceptions.py         # Custom exceptions
│   └── main.py               # FastAPI app factory
├── tests/                    # Test suite
├── requirements.txt          # Python dependencies
└── main.py                   # Entry point
```

## Getting Started

### Installation

```bash
cd services
pip install -r requirements.txt
```

### Running the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
pytest tests/
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Features

- ✅ Modular API structure (v1, v2, etc.)
- ✅ Async/await support
- ✅ Request/response validation with Pydantic
- ✅ Custom exception handling
- ✅ Logging middleware
- ✅ Configuration management
- ✅ Unit test setup
- ✅ Health check endpoint

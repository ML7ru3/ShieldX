# ShieldX Web

Web platform for the **ShieldX** cybersecurity ecosystem — a centralized dashboard for monitoring agent endpoints, managing malware alerts, and controlling domain whitelists.

## Architecture

```
ShieldX_web/
├── backend/          # FastAPI (Python) REST API
└── frontend/         # React + TypeScript + Vite + Chakra UI
```

### Backend (FastAPI)

- **Database:** MySQL via SQLModel/SQLAlchemy
- **Endpoints:**
  - `/heartbeat/` — Agent health monitoring & stale agent detection (via APScheduler)
  - `/report-malware/` — Malware alert ingestion
  - `/domain/whitelist/` — Full CRUD for whitelisted domains
- **Run:** `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

### Frontend (React + Vite)

- **UI:** Chakra UI + Framer Motion
- **HTTP Client:** Axios
- **Run:** `npm run dev` (served at `http://localhost:5173`)
- **Build:** `npm run build`

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Configure .env with DATABASE_URL, then:
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

API docs (Swagger) at `http://localhost:8000/docs`.

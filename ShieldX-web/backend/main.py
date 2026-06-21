from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Agent, MalwareAlert, WhitelistDomain
from sqlmodel import SQLModel, Session
from routes import heartbeat, malware, whitelist
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def check_stale_agents():
    with Session(engine) as session:
        heartbeat.mark_stale_agents_offline(session)

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    scheduler.add_job(check_stale_agents, "interval", minutes=1, id="check_agents_offline")
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(heartbeat.router, prefix="/heartbeat", tags=["heartbeat"])
app.include_router(malware.router, prefix="/report-malware", tags=["malware"])
app.include_router(whitelist.router, prefix="/domain/whitelist", tags=["whitelist"])

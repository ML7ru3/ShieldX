from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, update
from database import get_session
from models import Agent
from schemas import AgentCreate, AgentRead
from datetime import datetime, timedelta
from typing import List

router = APIRouter()

HEARTBEAT_TIMEOUT_MINUTES = 5

def mark_stale_agents_offline(session: Session):
    cutoff = datetime.utcnow() - timedelta(minutes=HEARTBEAT_TIMEOUT_MINUTES)
    stmt = (
        update(Agent)
        .where(Agent.last_seen < cutoff)
        .where(Agent.status != "offline")
        .values(status="offline")
    )
    session.execute(stmt)
    session.commit()

@router.get("/", response_model=List[AgentRead])
def list_agents(*, session: Session = Depends(get_session)):
    mark_stale_agents_offline(session)
    agents = session.exec(select(Agent)).all()
    return agents

@router.post("/", response_model=AgentRead)
def receive_heartbeat(*, session: Session = Depends(get_session), agent_data: AgentCreate):
    db_agent = session.exec(select(Agent).where(Agent.agent_id == agent_data.agent_id)).first()

    if db_agent:
        db_agent.last_seen = datetime.utcnow()
        db_agent.hostname = agent_data.hostname
        db_agent.ip = agent_data.ip
        db_agent.status = "active"
    else:
        db_agent = Agent.model_validate(agent_data)
        db_agent.first_seen = datetime.utcnow()
        db_agent.last_seen = datetime.utcnow()
        db_agent.status = "active"

    session.add(db_agent)
    session.commit()
    session.refresh(db_agent)
    return db_agent

from sqlmodel import Field, SQLModel, Relationship
from typing import List, Optional
from datetime import datetime

class Agent(SQLModel, table=True):
    agent_id: str = Field(primary_key=True, index=True)
    hostname: str
    ip: str
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    status: str = Field(default="active")

    malware_alerts: List["MalwareAlert"] = Relationship(back_populates="agent")

class MalwareAlert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: str = Field(index=True, foreign_key="agent.agent_id")
    malware_type: str
    details: Optional[str] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    agent: Agent = Relationship(back_populates="malware_alerts")

class WhitelistDomain(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str = Field(unique=True, index=True)
    date_added: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

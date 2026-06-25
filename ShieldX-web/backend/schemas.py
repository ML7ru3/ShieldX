from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- Agent Schemas ---
class AgentBase(BaseModel):
    agent_id: str
    hostname: str
    ip: str

class AgentCreate(AgentBase):
    pass

class AgentUpdate(AgentBase):
    hostname: Optional[str] = None
    ip: Optional[str] = None
    status: Optional[str] = None

class AgentRead(AgentBase):
    first_seen: datetime
    last_seen: datetime
    status: str

    class Config:
        from_attributes = True

# --- MalwareAlert Schemas ---
class MalwareAlertBase(BaseModel):
    agent_id: str
    malware_type: str
    details: Optional[str] = None

class MalwareAlertCreate(MalwareAlertBase):
    pass

class MalwareAlertRead(MalwareAlertBase):
    id: int
    detected_at: datetime

    class Config:
        from_attributes = True

# --- WhitelistDomain Schemas ---
class WhitelistDomainBase(BaseModel):
    domain: str
    notes: Optional[str] = None

class WhitelistDomainCreate(WhitelistDomainBase):
    pass

class WhitelistDomainUpdate(WhitelistDomainBase):
    domain: Optional[str] = None
    notes: Optional[str] = None

class WhitelistDomainRead(WhitelistDomainBase):
    id: int
    date_added: datetime

    class Config:
        from_attributes = True

class WhitelistDomainsResponse(BaseModel):
    domains: List[WhitelistDomainRead]
    whitelist_enabled: bool = True

# --- WhitelistConfig Schemas ---
class WhitelistConfigToggle(BaseModel):
    enabled: bool

# --- RecentDomain Schemas ---
class RecentDomainBase(BaseModel):
    agent_id: str
    domain: str
    ip: str = ""

class RecentDomainCreate(BaseModel):
    domains: List[RecentDomainBase]

class RecentDomainRead(BaseModel):
    id: int
    agent_id: str
    domain: str
    ip: str
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True

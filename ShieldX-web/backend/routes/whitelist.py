from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import WhitelistDomain, WhitelistConfig
from schemas import WhitelistDomainCreate, WhitelistDomainRead, WhitelistDomainUpdate, WhitelistDomainsResponse, WhitelistConfigToggle

router = APIRouter()

@router.get("/", response_model=WhitelistDomainsResponse)
def get_whitelist_domains(*, session: Session = Depends(get_session)):
    domains = session.exec(select(WhitelistDomain)).all()
    config = session.get(WhitelistConfig, 1)
    return {"domains": domains, "whitelist_enabled": config.enabled if config else True}

@router.get("/toggle")
def get_whitelist_toggle(*, session: Session = Depends(get_session)):
    config = session.get(WhitelistConfig, 1)
    return {"enabled": config.enabled if config else True}

@router.put("/toggle")
def set_whitelist_toggle(*, session: Session = Depends(get_session), body: WhitelistConfigToggle):
    config = session.get(WhitelistConfig, 1)
    if not config:
        config = WhitelistConfig(id=1, enabled=body.enabled)
    else:
        config.enabled = body.enabled
    session.add(config)
    session.commit()
    session.refresh(config)
    return {"enabled": config.enabled}

@router.post("/", response_model=WhitelistDomainRead)
def create_whitelist_domain(
    *, session: Session = Depends(get_session), domain_create: WhitelistDomainCreate
):
    db_domain = session.exec(select(WhitelistDomain).where(WhitelistDomain.domain == domain_create.domain)).first()
    if db_domain:
        raise HTTPException(status_code=400, detail="Domain already whitelisted")

    db_domain = WhitelistDomain.model_validate(domain_create)
    session.add(db_domain)
    session.commit()
    session.refresh(db_domain)
    return db_domain

@router.put("/{domain_id}", response_model=WhitelistDomainRead)
def update_whitelist_domain(
    *, session: Session = Depends(get_session), domain_id: int, domain_update: WhitelistDomainUpdate
):
    db_domain = session.get(WhitelistDomain, domain_id)
    if not db_domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    if domain_update.domain and domain_update.domain != db_domain.domain:
        existing_domain = session.exec(select(WhitelistDomain).where(WhitelistDomain.domain == domain_update.domain)).first()
        if existing_domain and existing_domain.id != domain_id:
            raise HTTPException(status_code=400, detail="Domain already whitelisted under another ID")

    domain_data = domain_update.model_dump(exclude_unset=True)
    db_domain.sqlmodel_update(domain_data)
    session.add(db_domain)
    session.commit()
    session.refresh(db_domain)
    return db_domain

@router.delete("/{domain_id}")
def delete_whitelist_domain(*, session: Session = Depends(get_session), domain_id: int):
    domain = session.get(WhitelistDomain, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    session.delete(domain)
    session.commit()
    return {"ok": True}

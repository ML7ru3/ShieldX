from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select
from database import get_session
from models import RecentDomain
from schemas import RecentDomainCreate, RecentDomainRead
from datetime import datetime

router = APIRouter()

@router.post("/")
def report_recent_domains(*, session: Session = Depends(get_session), body: RecentDomainCreate):
    now = datetime.utcnow()
    count = 0
    for entry in body.domains:
        existing = session.exec(
            select(RecentDomain).where(
                RecentDomain.agent_id == entry.agent_id,
                RecentDomain.domain == entry.domain,
            )
        ).first()
        if existing:
            existing.last_seen = now
            if entry.ip:
                existing.ip = entry.ip
        else:
            existing = RecentDomain(
                agent_id=entry.agent_id,
                domain=entry.domain,
                ip=entry.ip,
                first_seen=now,
                last_seen=now,
            )
        session.add(existing)
        count += 1
    session.commit()
    return {"updated": count}

@router.get("/{agent_id}", response_model=List[RecentDomainRead])
def get_recent_domains(*, session: Session = Depends(get_session), agent_id: str):
    domains = session.exec(
        select(RecentDomain)
        .where(RecentDomain.agent_id == agent_id)
        .order_by(RecentDomain.last_seen.desc())
    ).all()
    return domains

@router.get("/{agent_id}/download")
def download_recent_domains(*, session: Session = Depends(get_session), agent_id: str):
    domains = session.exec(
        select(RecentDomain)
        .where(RecentDomain.agent_id == agent_id)
        .order_by(RecentDomain.last_seen.desc())
    ).all()

    lines = [
        f"# ShieldX Recent Domains Report",
        f"# Agent: {agent_id}",
        f"# Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"#",
        f"# {'Domain':<35} {'IP':<22} {'Last Seen':<25}",
        f"# {'─'*35} {'─'*22} {'─'*25}",
    ]
    for d in domains:
        last_seen_str = d.last_seen.strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"  {d.domain:<35} {d.ip:<22} {last_seen_str:<25}")

    lines.append(f"\n# Total: {len(domains)} domains")
    content = "\n".join(lines)
    return PlainTextResponse(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=recent_domains_{agent_id}.log"},
    )

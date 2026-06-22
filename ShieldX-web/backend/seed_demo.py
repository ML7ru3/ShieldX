"""
Seed script: populates the database with demo data for all three tables.
Run with: python seed_demo.py
Requires: MySQL running (docker-compose up -d) and tables created.
"""
import random
from datetime import datetime, timedelta
from sqlmodel import Session, select
from database import engine
from models import Agent, MalwareAlert, WhitelistDomain

DEMO_AGENTS = [
    {"agent_id": "trung-vm-01", "hostname": "trung-vm-01", "ip": "192.168.1.101"},
    {"agent_id": "trung-vm-02", "hostname": "desktop-lab-02", "ip": "192.168.1.102"},
    {"agent_id": "server-prod-01", "hostname": "server-prod-01", "ip": "10.0.0.50"},
    {"agent_id": "laptop-dev-01", "hostname": "laptop-dev-01", "ip": "192.168.1.201"},
]

DEMO_DOMAINS = [
    {"domain": "dns.google", "notes": "Google Public DNS (DoH)"},
    {"domain": "cloudflare-dns.com", "notes": "Cloudflare 1.1.1.1 (DoH)"},
    {"domain": "dns.quad9.net", "notes": "Quad9 DNS (DoH)"},
    {"domain": "dns.opendns.com", "notes": "OpenDNS (DoH)"},
    {"domain": "dns.umbrella.com", "notes": "Cisco Umbrella (DoH)"},
    {"domain": "doh.powerdns.org", "notes": "PowerDNS (DoH)"},
    {"domain": "doh.securedns.eu", "notes": "SecureDNS Europe (DoH)"},
]

MALWARE_TYPES = [
    "doh_tunnel", "data_exfiltration", "c2_communication",
    "dns_tunneling", "encrypted_c2", "doh_malware"
]

MALWARE_DETAILS_TEMPLATES = [
    "Suspicious DoH traffic detected to known C2 server {dst_ip}:{dst_port}",
    "Anomalous DNS-over-HTTPS pattern with high entropy query names",
    "Potential data exfiltration via DNS tunneling to {dst_ip}",
    "Malicious DoH flow with abnormal packet timing characteristics",
    "C2 communication detected over encrypted DNS channel to {dst_ip}",
    "DNS-over-HTTPS traffic matching known malware signature",
]

SAMPLE_FLOW_FEATURES = {
    "FlowBytesSent": 14500,
    "FlowSentRate": 120.5,
    "FlowBytesReceived": 8900,
    "FlowReceivedRate": 74.2,
    "PacketLengthMean": 128.4,
    "PacketLengthVariance": 2048.3,
    "PacketLengthStdDev": 45.3,
    "PacketTimeMean": 0.052,
    "PacketTimeVariance": 0.018,
    "ResponseTimeMean": 0.038,
    "ResponseTimeStdDev": 0.021,
}


def seed():
    with Session(engine) as session:
        existing_agents = session.exec(select(Agent)).all()
        if existing_agents:
            print(f"Database already has {len(existing_agents)} agents. Deleting all existing data first...")
            for alert in session.exec(select(MalwareAlert)).all():
                session.delete(alert)
            for domain in session.exec(select(WhitelistDomain)).all():
                session.delete(domain)
            for agent in existing_agents:
                session.delete(agent)
            session.commit()
            print("Cleared existing data.")

        for a in DEMO_AGENTS:
            agent = Agent(
                agent_id=a["agent_id"],
                hostname=a["hostname"],
                ip=a["ip"],
                first_seen=datetime.utcnow() - timedelta(days=random.randint(1, 14)),
                last_seen=datetime.utcnow() - timedelta(minutes=random.randint(0, 30)),
                status="active",
            )
            session.add(agent)
        session.commit()
        print(f"Inserted {len(DEMO_AGENTS)} agents.")

        for d in DEMO_DOMAINS:
            domain = WhitelistDomain(
                domain=d["domain"],
                notes=d["notes"],
                date_added=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            )
            session.add(domain)
        session.commit()
        print(f"Inserted {len(DEMO_DOMAINS)} whitelist domains.")

        agents = session.exec(select(Agent)).all()
        alerts = []
        for _ in range(50):
            agent = random.choice(agents)
            dst_ip = f"{random.randint(10, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
            dst_port = random.choice([443, 8443, 2053, 2083])
            malware_type = random.choice(MALWARE_TYPES)
            details = random.choice(MALWARE_DETAILS_TEMPLATES).format(dst_ip=dst_ip, dst_port=dst_port)

            flow_features = SAMPLE_FLOW_FEATURES.copy()
            flow_features["src_ip"] = agent.ip
            flow_features["dst_ip"] = dst_ip
            flow_features["dst_port"] = dst_port

            import json
            alert = MalwareAlert(
                agent_id=agent.agent_id,
                malware_type=malware_type,
                details=json.dumps({"description": details, "flow": flow_features}),
                detected_at=datetime.utcnow() - timedelta(
                    hours=random.randint(1, 168),
                    minutes=random.randint(0, 59),
                ),
            )
            session.add(alert)
            alerts.append(alert)

        session.commit()
        print(f"Inserted {len(alerts)} malware alerts.")
        print("Done! Database is ready for demo.")


if __name__ == "__main__":
    seed()

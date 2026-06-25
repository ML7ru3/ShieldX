export interface Agent {
  agent_id: string;
  hostname: string;
  ip: string;
  first_seen: string;
  last_seen: string;
  status: string;
}

export interface MalwareAlert {
  id: number;
  agent_id: string;
  malware_type: string;
  details: string | null;
  detected_at: string;
}

export interface WhitelistDomain {
  id: number;
  domain: string;
  date_added: string;
  notes: string | null;
}

export interface RecentDomain {
  id: number;
  agent_id: string;
  domain: string;
  ip: string;
  first_seen: string;
  last_seen: string;
}

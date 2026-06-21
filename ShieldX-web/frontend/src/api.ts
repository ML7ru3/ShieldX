import axios from 'axios';
import type { Agent, MalwareAlert, WhitelistDomain } from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export const heartbeatApi = {
  send: (data: { agent_id: string; hostname: string; ip: string }) =>
    api.post<Agent>('/heartbeat/', data),
};

export const malwareApi = {
  report: (data: { agent_id: string; malware_type: string; details?: string }) =>
    api.post<MalwareAlert>('/report-malware/', data),
};

export const whitelistApi = {
  getAll: () => api.get<{ domains: WhitelistDomain[] }>('/domain/whitelist/'),
  create: (data: { domain: string; notes?: string }) =>
    api.post<WhitelistDomain>('/domain/whitelist/', data),
  update: (id: number, data: { domain?: string; notes?: string }) =>
    api.put<WhitelistDomain>(`/domain/whitelist/${id}`, data),
  delete: (id: number) => api.delete(`/domain/whitelist/${id}`),
};

export default api;

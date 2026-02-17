import axios from "axios";

const api = axios.create({ baseURL: "/api" });

// --- Types ---

export interface Run {
  id: string;
  brief: string;
  status: string;
  current_stage: string;
  created_at: string;
  updated_at: string;
}

export interface Artifact {
  id: string;
  run_id: string;
  agent: string;
  type: string;
  content: Record<string, unknown>;
  parent_ids: string[];
  created_at: string;
}

export interface DecisionLogEntry {
  id: number;
  run_id: string;
  agent: string;
  action: string;
  details: Record<string, unknown>;
  timestamp: string;
}

export interface HitlGate {
  id: number;
  run_id: string;
  stage: string;
  status: string;
  feedback: string | null;
  created_at: string;
  resolved_at: string | null;
}

// --- API functions ---

export async function createRun(brief: string): Promise<Run> {
  const { data } = await api.post<Run>("/runs", { brief });
  return data;
}

export async function listRuns(): Promise<Run[]> {
  const { data } = await api.get<Run[]>("/runs");
  return data;
}

export async function getRun(runId: string): Promise<Run> {
  const { data } = await api.get<Run>(`/runs/${runId}`);
  return data;
}

export async function getRunStatus(runId: string) {
  const { data } = await api.get<{ id: string; status: string; current_stage: string }>(`/runs/${runId}/status`);
  return data;
}

export async function getArtifacts(runId: string): Promise<Artifact[]> {
  const { data } = await api.get<Artifact[]>(`/runs/${runId}/artifacts`);
  return data;
}

export async function getArtifact(runId: string, artifactId: string): Promise<Artifact> {
  const { data } = await api.get<Artifact>(`/runs/${runId}/artifacts/${artifactId}`);
  return data;
}

export async function getCurrentHitl(runId: string): Promise<HitlGate | null> {
  const { data } = await api.get<HitlGate | null>(`/runs/${runId}/hitl/current`);
  return data;
}

export async function approveHitl(runId: string) {
  const { data } = await api.post(`/runs/${runId}/hitl/approve`);
  return data;
}

export async function rejectHitl(runId: string) {
  const { data } = await api.post(`/runs/${runId}/hitl/reject`);
  return data;
}

export async function requestChangesHitl(runId: string, feedback: string) {
  const { data } = await api.post(`/runs/${runId}/hitl/request-changes`, { feedback });
  return data;
}

export async function getDecisionLogs(runId: string): Promise<DecisionLogEntry[]> {
  const { data } = await api.get<DecisionLogEntry[]>(`/runs/${runId}/logs`);
  return data;
}

export async function getDiagram(runId: string, type: "er" | "sequence") {
  const { data } = await api.get(`/runs/${runId}/diagrams/${type}`);
  return data;
}

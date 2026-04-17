import { apiClient } from "./client";
import type { Run, RunEvent, Uuid } from "../types/api";

export async function listRuns(params?: {
  config_id?: Uuid;
  status?: string;
  limit?: number;
}): Promise<Run[]> {
  const { data } = await apiClient.get<Run[]>("/api/v1/runs", { params });
  return data;
}

export async function getRun(id: Uuid): Promise<Run> {
  const { data } = await apiClient.get<Run>(`/api/v1/runs/${id}`);
  return data;
}

export async function triggerRun(configId: Uuid): Promise<Run> {
  const { data } = await apiClient.post<Run>(
    `/api/v1/configs/${configId}/runs`,
  );
  return data;
}

export async function listRunEvents(
  runId: Uuid,
  afterId = 0,
): Promise<RunEvent[]> {
  const { data } = await apiClient.get<RunEvent[]>(
    `/api/v1/runs/${runId}/events`,
    { params: { after_id: afterId } },
  );
  return data;
}

export async function cancelRun(id: Uuid): Promise<void> {
  await apiClient.post(`/api/v1/runs/${id}/cancel`);
}

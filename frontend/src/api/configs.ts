import { apiClient } from "./client";
import type {
  ReportConfig,
  ReportConfigCreate,
  ReportConfigUpdate,
  Uuid,
} from "../types/api";

export async function listConfigs(params?: {
  active?: boolean;
}): Promise<ReportConfig[]> {
  const { data } = await apiClient.get<ReportConfig[]>("/api/v1/configs", {
    params,
  });
  return data;
}

export async function getConfig(id: Uuid): Promise<ReportConfig> {
  const { data } = await apiClient.get<ReportConfig>(`/api/v1/configs/${id}`);
  return data;
}

export async function createConfig(
  payload: ReportConfigCreate,
): Promise<ReportConfig> {
  const { data } = await apiClient.post<ReportConfig>(
    "/api/v1/configs",
    payload,
  );
  return data;
}

export async function updateConfig(
  id: Uuid,
  payload: ReportConfigUpdate,
): Promise<ReportConfig> {
  const { data } = await apiClient.put<ReportConfig>(
    `/api/v1/configs/${id}`,
    payload,
  );
  return data;
}

export async function deleteConfig(id: Uuid): Promise<void> {
  await apiClient.delete(`/api/v1/configs/${id}`);
}

export async function testDryRun(id: Uuid): Promise<unknown> {
  const { data } = await apiClient.post(`/api/v1/configs/${id}/test`);
  return data;
}

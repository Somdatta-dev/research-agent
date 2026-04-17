import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as api from "../api/configs";
import type {
  ReportConfigCreate,
  ReportConfigUpdate,
  Uuid,
} from "../types/api";

const KEY = ["configs"] as const;

export function useConfigsList(params?: { active?: boolean }) {
  return useQuery({
    queryKey: [...KEY, "list", params ?? {}],
    queryFn: () => api.listConfigs(params),
  });
}

export function useConfig(id?: Uuid) {
  return useQuery({
    queryKey: [...KEY, "detail", id],
    queryFn: () => api.getConfig(id!),
    enabled: Boolean(id),
  });
}

export function useCreateConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ReportConfigCreate) => api.createConfig(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdateConfig(id: Uuid) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ReportConfigUpdate) => api.updateConfig(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useDeleteConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: Uuid) => api.deleteConfig(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useTestDryRun() {
  return useMutation({ mutationFn: (id: Uuid) => api.testDryRun(id) });
}

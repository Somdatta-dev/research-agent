import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as api from "../api/runs";
import type { Uuid } from "../types/api";

const KEY = ["runs"] as const;

export function useRunsList(params?: {
  config_id?: Uuid;
  status?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: [...KEY, "list", params ?? {}],
    queryFn: () => api.listRuns(params),
    refetchInterval: 10_000,
  });
}

export function useRun(id?: Uuid) {
  return useQuery({
    queryKey: [...KEY, "detail", id],
    queryFn: () => api.getRun(id!),
    enabled: Boolean(id),
  });
}

export function useTriggerRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (configId: Uuid) => api.triggerRun(configId),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useCancelRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: Uuid) => api.cancelRun(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

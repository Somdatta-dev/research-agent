import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { useSettingsStore } from "../store/settings";
import { cn } from "../lib/utils";

export function ConnectionBadge() {
  const backendUrl = useSettingsStore((s) => s.backendUrl);
  const q = useQuery({
    queryKey: ["health", backendUrl],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/health");
      return res.data as { status?: string };
    },
    refetchInterval: 5_000,
  });

  const ok = q.data?.status === "ok";
  const err = q.isError;
  const color = ok
    ? "bg-emerald-500"
    : err
      ? "bg-red-500"
      : "bg-amber-500";
  const label = ok ? "Connected" : err ? "Disconnected" : "Connecting";

  return (
    <div
      className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-xs"
      title={backendUrl}
    >
      <span className={cn("h-2 w-2 rounded-full", color)} aria-hidden />
      <span className="font-medium">{label}</span>
      <span className="text-muted-foreground">{backendUrl}</span>
    </div>
  );
}

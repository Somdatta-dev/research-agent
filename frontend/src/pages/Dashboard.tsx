import { Link } from "react-router-dom";
import { Play, Plus } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useConfigsList } from "../hooks/useReportConfig";
import { useRunsList, useTriggerRun } from "../hooks/useRuns";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import type { Run, RunStatus } from "../types/api";

const statusTone: Record<RunStatus, "success" | "warning" | "danger" | "muted" | "default"> = {
  completed: "success",
  running: "default",
  pending: "warning",
  failed: "danger",
  cancelled: "muted",
};

function formatRel(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return formatDistanceToNow(new Date(iso), { addSuffix: true });
  } catch {
    return "—";
  }
}

export default function Dashboard() {
  const configs = useConfigsList({ active: true });
  const runs = useRunsList({ limit: 20 });
  const trigger = useTriggerRun();

  const items = configs.data ?? [];
  const recent: Run[] = runs.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Active report configs and recent runs.
          </p>
        </div>
        <Link to="/configs/new">
          <Button>
            <Plus className="h-4 w-4" />
            New config
          </Button>
        </Link>
      </div>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.length === 0 && !configs.isLoading && (
          <Card className="col-span-full">
            <CardContent className="p-6 text-sm text-muted-foreground">
              No active configs yet.{" "}
              <Link
                to="/configs/new"
                className="font-medium text-primary underline-offset-4 hover:underline"
              >
                Create one
              </Link>
              .
            </CardContent>
          </Card>
        )}
        {items.map((c) => {
          const lastRun = recent.find((r) => r.config_id === c.id);
          return (
            <Card key={c.id}>
              <CardHeader>
                <CardTitle>{c.name}</CardTitle>
                <CardDescription className="line-clamp-2">
                  {c.topic}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    <span className="font-mono">{c.schedule_cron}</span>{" "}
                    <span className="opacity-70">({c.timezone})</span>
                  </span>
                  {lastRun && (
                    <Badge tone={statusTone[lastRun.status] ?? "default"}>
                      {lastRun.status}
                    </Badge>
                  )}
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    Last run:{" "}
                    <span className="text-foreground">
                      {formatRel(lastRun?.created_at)}
                    </span>
                  </span>
                  <span>{c.recipients.length} recipient(s)</span>
                </div>
                <div className="flex gap-2 pt-1">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => trigger.mutate(c.id)}
                    disabled={trigger.isPending}
                  >
                    <Play className="h-3.5 w-3.5" />
                    Run now
                  </Button>
                  <Link to={`/configs/${c.id}`} className="flex-1">
                    <Button variant="outline" size="sm" className="w-full">
                      Edit
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold">Recent runs</h2>
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-2 font-medium">Started</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium">Trigger</th>
                <th className="px-4 py-2 font-medium">Node</th>
                <th className="px-4 py-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {recent.length === 0 && (
                <tr>
                  <td
                    className="px-4 py-6 text-center text-xs text-muted-foreground"
                    colSpan={5}
                  >
                    No runs yet.
                  </td>
                </tr>
              )}
              {recent.map((r) => (
                <tr key={r.id} className="border-t border-border">
                  <td className="px-4 py-2 text-muted-foreground">
                    {formatRel(r.created_at)}
                  </td>
                  <td className="px-4 py-2">
                    <Badge tone={statusTone[r.status] ?? "default"}>
                      {r.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">
                    {r.trigger}
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">
                    {r.current_node ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <Link
                      to={`/runs/${r.id}`}
                      className="text-xs font-medium text-primary underline-offset-4 hover:underline"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

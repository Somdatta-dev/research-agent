import { Link } from "react-router-dom";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import {
  useConfigsList,
  useDeleteConfig,
} from "../hooks/useReportConfig";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";

function formatRel(iso: string): string {
  try {
    return formatDistanceToNow(new Date(iso), { addSuffix: true });
  } catch {
    return "—";
  }
}

export default function ConfigList() {
  const configs = useConfigsList();
  const del = useDeleteConfig();
  const items = configs.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            Report configs
          </h1>
          <p className="text-sm text-muted-foreground">
            Recipes for the daily research agent. Inactive configs are kept
            for history but won't run.
          </p>
        </div>
        <Link to="/configs/new">
          <Button>
            <Plus className="h-4 w-4" />
            New config
          </Button>
        </Link>
      </div>

      <div className="overflow-hidden rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-2 font-medium">Name</th>
              <th className="px-4 py-2 font-medium">Schedule</th>
              <th className="px-4 py-2 font-medium">Recipients</th>
              <th className="px-4 py-2 font-medium">Status</th>
              <th className="px-4 py-2 font-medium">Updated</th>
              <th className="px-4 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && !configs.isLoading && (
              <tr>
                <td
                  className="px-4 py-8 text-center text-xs text-muted-foreground"
                  colSpan={6}
                >
                  No configs yet.
                </td>
              </tr>
            )}
            {items.map((c) => (
              <tr key={c.id} className="border-t border-border">
                <td className="px-4 py-2 font-medium">{c.name}</td>
                <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                  {c.schedule_cron}{" "}
                  <span className="opacity-70">({c.timezone})</span>
                </td>
                <td className="px-4 py-2 text-muted-foreground">
                  {c.recipients.length}
                </td>
                <td className="px-4 py-2">
                  <Badge tone={c.active ? "success" : "muted"}>
                    {c.active ? "active" : "inactive"}
                  </Badge>
                </td>
                <td className="px-4 py-2 text-xs text-muted-foreground">
                  {formatRel(c.updated_at)}
                </td>
                <td className="px-4 py-2">
                  <div className="flex justify-end gap-2">
                    <Link to={`/configs/${c.id}`}>
                      <Button size="sm" variant="outline">
                        <Pencil className="h-3.5 w-3.5" />
                        Edit
                      </Button>
                    </Link>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        if (
                          window.confirm(
                            `Deactivate "${c.name}"? It can be re-enabled later.`,
                          )
                        ) {
                          del.mutate(c.id);
                        }
                      }}
                      disabled={del.isPending}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

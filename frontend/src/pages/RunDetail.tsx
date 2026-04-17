import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Download, Search } from "lucide-react";
import { useRun } from "../hooks/useRuns";
import { useRunStream } from "../hooks/useRunStream";
import { RunTimeline } from "../components/RunTimeline";
import { EventLogPane } from "../components/EventLogPane";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { useSettingsStore } from "../store/settings";
import type { RunStatus } from "../types/api";

const statusTone: Record<
  RunStatus,
  "success" | "warning" | "danger" | "muted" | "default"
> = {
  completed: "success",
  running: "default",
  pending: "warning",
  failed: "danger",
  cancelled: "muted",
};

export default function RunDetail() {
  const { id } = useParams<{ id: string }>();
  const run = useRun(id);
  const { events, connected } = useRunStream(id);
  const backendUrl = useSettingsStore((s) => s.backendUrl);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const pdfRendered = events.find((e) => e.type === "pdf_rendered");
  const r = run.data;

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-3">
          <Link to="/">
            <Button size="icon" variant="ghost">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-sm font-semibold">
              Run {id?.slice(0, 8)}...
            </h1>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {r && (
                <Badge tone={statusTone[r.status] ?? "default"}>
                  {r.status}
                </Badge>
              )}
              {r?.current_node && (
                <span className="font-mono">{r.current_node}</span>
              )}
              <span>{connected ? "WS connected" : "WS disconnected"}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2 top-2 h-4 w-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter events..."
              className="h-8 w-48 pl-8 text-xs"
            />
          </div>
          {r?.pdf_path && (
            <a
              href={`${backendUrl.replace(/\/+$/, "")}/api/v1/reports/${id}.pdf`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button size="sm" variant="secondary">
                <Download className="h-3.5 w-3.5" />
                PDF
              </Button>
            </a>
          )}
        </div>
      </div>

      <div className="flex min-h-0 flex-1">
        <aside className="w-48 shrink-0 overflow-auto border-r border-border p-3">
          <RunTimeline
            events={events}
            selectedNode={selectedNode}
            onSelect={setSelectedNode}
          />
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <div className="min-h-0 flex-1 overflow-hidden">
            <EventLogPane
              events={events}
              filterNode={selectedNode}
              searchQuery={search}
            />
          </div>

          {pdfRendered && (
            <div className="border-t border-border bg-muted/30 px-4 py-3 text-xs">
              PDF rendered:{" "}
              {String((pdfRendered.payload as Record<string, unknown>)?.pages ?? "?")}{" "}
              pages{" — "}
              <a
                href={`${backendUrl.replace(/\/+$/, "")}/api/v1/reports/${id}.pdf`}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-primary underline-offset-4 hover:underline"
              >
                Download
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

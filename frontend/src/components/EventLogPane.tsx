import { useEffect, useRef, useState } from "react";
import { format } from "date-fns";
import { cn } from "../lib/utils";
import type { RunEvent } from "../types/api";

const TYPE_COLORS: Record<string, string> = {
  run_started: "text-blue-500",
  run_completed: "text-emerald-500",
  run_failed: "text-red-500",
  node_completed: "text-emerald-600",
  node_failed: "text-red-500",
  search_query: "text-amber-600",
  search_results: "text-amber-500",
  dedup_summary: "text-purple-500",
  enrichment_start: "text-cyan-500",
  enrichment_done: "text-cyan-600",
  synthesize_start: "text-indigo-500",
  section_drafted: "text-indigo-600",
  write_done: "text-violet-500",
  pdf_rendered: "text-green-600",
  email_sent: "text-emerald-600",
  log: "text-muted-foreground",
};

function payloadSummary(payload: Record<string, unknown>): string {
  const parts: string[] = [];
  for (const [k, v] of Object.entries(payload)) {
    if (k === "type") continue;
    const s = typeof v === "string" ? v : JSON.stringify(v);
    parts.push(`${k}=${s}`);
  }
  return parts.join("  ");
}

interface Props {
  events: RunEvent[];
  filterNode: string | null;
  searchQuery: string;
}

export function EventLogPane({ events, filterNode, searchQuery }: Props) {
  const endRef = useRef<HTMLDivElement>(null);
  const [paused, setPaused] = useState(false);

  const filtered = events.filter((e) => {
    if (filterNode && e.node !== filterNode && !e.node?.startsWith(filterNode))
      return false;
    if (searchQuery) {
      const text =
        `${e.type} ${e.node ?? ""} ${JSON.stringify(e.payload)}`.toLowerCase();
      if (!text.includes(searchQuery.toLowerCase())) return false;
    }
    return true;
  });

  useEffect(() => {
    if (!paused) {
      endRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [filtered.length, paused]);

  return (
    <div
      className="h-full overflow-auto font-mono text-xs"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <table className="w-full">
        <tbody>
          {filtered.map((e, idx) => (
            <tr
              key={e.id ?? idx}
              className="border-b border-border/50 hover:bg-muted/30"
            >
              <td className="whitespace-nowrap px-2 py-1 text-muted-foreground">
                {e.ts ? format(new Date(e.ts), "HH:mm:ss.SSS") : "\u2014"}
              </td>
              <td
                className={cn(
                  "whitespace-nowrap px-2 py-1 font-medium",
                  TYPE_COLORS[e.type] ?? "text-foreground",
                )}
              >
                {e.type}
              </td>
              <td className="whitespace-nowrap px-2 py-1 text-muted-foreground">
                {e.node ?? ""}
              </td>
              <td className="px-2 py-1 text-muted-foreground">
                {payloadSummary(e.payload ?? {})}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div ref={endRef} />
    </div>
  );
}

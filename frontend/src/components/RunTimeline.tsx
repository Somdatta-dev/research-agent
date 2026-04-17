import { CheckCircle, Circle, Loader2, XCircle } from "lucide-react";
import { cn } from "../lib/utils";
import type { RunEvent } from "../types/api";

const NODES = [
  "plan",
  "research_one",
  "dedup",
  "enrich_one",
  "synthesize",
  "write",
  "render_pdf",
  "deliver",
];

type NodeState = "pending" | "running" | "done" | "failed";

function deriveNodeStates(events: RunEvent[]): Record<string, NodeState> {
  const states: Record<string, NodeState> = {};
  for (const node of NODES) states[node] = "pending";

  for (const e of events) {
    const node = e.node;
    if (!node || typeof node !== "string") continue;
    const base = NODES.find((n) => node.startsWith(n)) ?? node;
    if (!(base in states)) states[base] = "pending";

    if (e.type === "node_completed" || e.type === "node_end") {
      states[base] = "done";
    } else if (e.type === "node_failed") {
      states[base] = "failed";
    } else if (states[base] === "pending") {
      states[base] = "running";
    }
  }
  return states;
}

const icons: Record<NodeState, React.ReactNode> = {
  pending: <Circle className="h-4 w-4 text-muted-foreground" />,
  running: <Loader2 className="h-4 w-4 animate-spin text-primary" />,
  done: <CheckCircle className="h-4 w-4 text-emerald-500" />,
  failed: <XCircle className="h-4 w-4 text-red-500" />,
};

interface Props {
  events: RunEvent[];
  selectedNode: string | null;
  onSelect: (node: string | null) => void;
}

export function RunTimeline({ events, selectedNode, onSelect }: Props) {
  const states = deriveNodeStates(events);

  return (
    <nav className="space-y-1">
      <button
        onClick={() => onSelect(null)}
        className={cn(
          "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors",
          selectedNode === null
            ? "bg-primary text-primary-foreground"
            : "text-muted-foreground hover:bg-accent",
        )}
      >
        All events
      </button>
      {NODES.map((node) => (
        <button
          key={node}
          onClick={() => onSelect(node)}
          className={cn(
            "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors",
            selectedNode === node
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-accent",
          )}
        >
          {icons[states[node] ?? "pending"]}
          <span className="font-mono text-xs">{node}</span>
        </button>
      ))}
    </nav>
  );
}

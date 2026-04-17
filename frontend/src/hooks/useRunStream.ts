import { useCallback, useEffect, useRef, useState } from "react";
import { listRunEvents } from "../api/runs";
import { createRunSocket } from "../api/ws";
import type { RunEvent } from "../types/api";

export function useRunStream(runId: string | undefined) {
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<{ close: () => void } | null>(null);

  const addEvent = useCallback((e: RunEvent) => {
    setEvents((prev) => {
      if (e.id && prev.some((p) => p.id === e.id)) return prev;
      return [...prev, e];
    });
  }, []);

  useEffect(() => {
    if (!runId) return;
    let cancelled = false;

    async function seed() {
      try {
        const history = await listRunEvents(runId!);
        if (!cancelled) setEvents(history);
      } catch {
        // will retry via WS
      }
      if (cancelled) return;

      socketRef.current = createRunSocket(
        runId!,
        (evt) => {
          if (!cancelled) addEvent(evt);
        },
        () => setConnected(false),
      );
      setConnected(true);
    }

    void seed();
    return () => {
      cancelled = true;
      socketRef.current?.close();
      socketRef.current = null;
      setConnected(false);
    };
  }, [runId, addEvent]);

  return { events, connected };
}

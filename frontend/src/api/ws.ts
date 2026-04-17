import { useSettingsStore } from "../store/settings";
import type { RunEvent } from "../types/api";

type EventCallback = (event: RunEvent) => void;

export function createRunSocket(
  runId: string,
  onEvent: EventCallback,
  onClose?: () => void,
): { close: () => void } {
  const raw = useSettingsStore.getState().backendUrl.replace(/\/+$/, "");
  const base = raw || window.location.origin;
  const wsBase = base.replace(/^http/, "ws");
  const url = `${wsBase}/api/v1/ws/runs/${runId}`;

  let ws: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let closed = false;
  let attempt = 0;

  function connect() {
    if (closed) return;
    ws = new WebSocket(url);

    ws.onopen = () => {
      attempt = 0;
    };

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data) as RunEvent;
        onEvent(data);
      } catch {
        // ignore malformed
      }
    };

    ws.onclose = () => {
      if (closed) {
        onClose?.();
        return;
      }
      attempt += 1;
      const delay = Math.min(1000 * 2 ** attempt, 30_000);
      reconnectTimer = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws?.close();
    };
  }

  connect();

  return {
    close() {
      closed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      ws?.close();
    },
  };
}

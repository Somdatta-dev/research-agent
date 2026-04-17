import { create } from "zustand";

const STORAGE_KEY = "market-insights.settings";
const DEFAULT_BACKEND_URL = "";

interface PersistedSettings {
  backendUrl: string;
  theme: "light" | "dark" | "system";
}

interface SettingsState extends PersistedSettings {
  hydrated: boolean;
  hydrate: () => Promise<void>;
  setBackendUrl: (url: string) => void;
  setTheme: (theme: PersistedSettings["theme"]) => void;
}

function readPersisted(): Partial<PersistedSettings> | null {
  if (typeof localStorage === "undefined") return null;
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Partial<PersistedSettings>;
  } catch {
    return null;
  }
}

function writePersisted(next: PersistedSettings): void {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  backendUrl: DEFAULT_BACKEND_URL,
  theme: "system",
  hydrated: false,
  hydrate: async () => {
    if (get().hydrated) return;
    const persisted = readPersisted();
    set({
      backendUrl: persisted?.backendUrl || DEFAULT_BACKEND_URL,
      theme: persisted?.theme || "system",
      hydrated: true,
    });
  },
  setBackendUrl: (url) => {
    set({ backendUrl: url });
    writePersisted({ backendUrl: url, theme: get().theme });
  },
  setTheme: (theme) => {
    set({ theme });
    writePersisted({ backendUrl: get().backendUrl, theme });
  },
}));

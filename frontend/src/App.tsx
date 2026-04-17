import { useEffect } from "react";
import { useSettingsStore } from "./store/settings";
import { AppRoutes } from "./routes";

export default function App() {
  const { hydrated, hydrate, theme } = useSettingsStore();

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (typeof document === "undefined") return;
    const root = document.documentElement;
    const resolved =
      theme === "system"
        ? window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light"
        : theme;
    root.classList.toggle("dark", resolved === "dark");
  }, [theme]);

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-sm text-muted-foreground">
        Loading…
      </div>
    );
  }

  return <AppRoutes />;
}

import { useSettingsStore } from "../store/settings";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { ConnectionBadge } from "../components/ConnectionBadge";

export default function Settings() {
  const { backendUrl, setBackendUrl, theme, setTheme } = useSettingsStore();

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Local desktop preferences. Stored on this machine only.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Backend</CardTitle>
          <CardDescription>
            The FastAPI instance this app talks to.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <Label htmlFor="backend">Backend URL</Label>
            <Input
              id="backend"
              type="url"
              value={backendUrl}
              onChange={(e) => setBackendUrl(e.target.value)}
              placeholder="http://localhost:8080"
              spellCheck={false}
            />
          </div>
          <div className="flex items-center justify-between">
            <ConnectionBadge />
            <p className="text-xs text-muted-foreground">Pings every 5s.</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Theme</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            {(["light", "dark", "system"] as const).map((t) => (
              <Button
                key={t}
                size="sm"
                variant={theme === t ? "primary" : "outline"}
                onClick={() => setTheme(t)}
              >
                {t}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

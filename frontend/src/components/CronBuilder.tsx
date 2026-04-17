import { useMemo } from "react";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { cn } from "../lib/utils";

const PRESETS: { label: string; cron: string }[] = [
  { label: "Daily 07:00", cron: "0 7 * * *" },
  { label: "Weekdays 07:00", cron: "0 7 * * 1-5" },
  { label: "Twice daily (07 & 17)", cron: "0 7,17 * * *" },
  { label: "Every Monday 08:00", cron: "0 8 * * 1" },
];

const CRON_RE =
  /^\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$/;

function humanize(cron: string): string | null {
  if (!CRON_RE.test(cron)) return null;
  const [min, hr, dom, mon, dow] = cron.trim().split(/\s+/);
  if (dom === "*" && mon === "*" && dow === "*")
    return `Every day at ${hr.padStart(2, "0")}:${min.padStart(2, "0")}`;
  if (dom === "*" && mon === "*" && dow === "1-5")
    return `Weekdays at ${hr.padStart(2, "0")}:${min.padStart(2, "0")}`;
  return null;
}

interface Props {
  cron: string;
  timezone: string;
  onCronChange: (v: string) => void;
  onTimezoneChange: (v: string) => void;
  error?: string;
}

export function CronBuilder({
  cron,
  timezone,
  onCronChange,
  onTimezoneChange,
  error,
}: Props) {
  const human = useMemo(() => humanize(cron), [cron]);

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-[1fr_200px] gap-3">
        <div>
          <Label htmlFor="schedule_cron">Cron expression</Label>
          <Input
            id="schedule_cron"
            value={cron}
            onChange={(e) => onCronChange(e.target.value)}
            placeholder="0 7 * * *"
            className={cn(error && "border-destructive")}
            spellCheck={false}
          />
        </div>
        <div>
          <Label htmlFor="timezone">Timezone (IANA)</Label>
          <Input
            id="timezone"
            value={timezone}
            onChange={(e) => onTimezoneChange(e.target.value)}
            placeholder="Asia/Kolkata"
            spellCheck={false}
          />
        </div>
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}

      <div className="text-xs text-muted-foreground">
        {human ? (
          <span>
            <span className="font-medium text-foreground">{human}</span>{" "}
            <span>({timezone})</span>
          </span>
        ) : (
          <span>5-field cron; minute hour day-of-month month day-of-week</span>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {PRESETS.map((p) => (
          <button
            key={p.cron}
            type="button"
            onClick={() => onCronChange(p.cron)}
            className="rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            {p.label}
          </button>
        ))}
      </div>
    </div>
  );
}

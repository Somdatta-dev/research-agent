import { NavLink, Outlet } from "react-router-dom";
import { LayoutDashboard, List, Settings2 } from "lucide-react";
import { cn } from "../lib/utils";
import { ConnectionBadge } from "./ConnectionBadge";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/configs", label: "Configs", icon: List, end: false },
  { to: "/settings", label: "Settings", icon: Settings2, end: false },
];

export function Layout() {
  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <aside className="w-56 shrink-0 border-r border-border bg-card/40">
        <div className="px-5 py-5">
          <div className="text-sm font-semibold tracking-tight">
            Market Insights
          </div>
          <div className="text-xs text-muted-foreground">v0.1.0</div>
        </div>
        <nav className="px-2 pb-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    "mb-1 flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                  )
                }
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-border px-6">
          <div className="text-sm text-muted-foreground">
            Daily autonomous research → LinkedIn PDF
          </div>
          <ConnectionBadge />
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

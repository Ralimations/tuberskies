import {
  LayoutDashboard,
  Sparkles,
  Zap,
  Upload,
  BarChart2,
  BookOpen,
  Music2,
  Vault,
  Settings,
} from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

const NAV_MAIN = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Create", path: "/create", icon: Sparkles },
  { label: "Optimize", path: "/optimize", icon: Zap },
  { label: "Publish", path: "/publish", icon: Upload },
  { label: "Analyze", path: "/analyze", icon: BarChart2 },
];

const NAV_LIBRARY = [
  { label: "Learn", path: "/learn", icon: BookOpen },
  { label: "Repertoire", path: "/repertoire", icon: Music2 },
  { label: "Vault", path: "/vault", icon: Vault },
];

export function Sidebar() {
  const location = useLocation();

  function isActive(path: string) {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  }

  return (
    <aside className="glass-panel rounded-[28px] border border-[var(--color-aria-border)] p-3 shadow-[0_18px_60px_rgba(2,8,23,0.28)]">
      <div className="flex items-center gap-3 rounded-[22px] border border-[var(--color-aria-border)] bg-white/4 px-4 py-4">
        <div className="gradient-btn flex h-11 w-11 items-center justify-center rounded-2xl shrink-0">
          <span className="font-mono text-sm font-black text-slate-950">A</span>
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold tracking-[0.18em] text-[var(--color-aria-muted)] uppercase">
            A.R.I.A.
          </p>
          <p className="text-lg font-semibold text-[var(--color-aria-ink)]">Creator cockpit</p>
        </div>
      </div>

      <nav className="space-y-6 px-1 py-5">
        <NavSection label="Workflows" items={NAV_MAIN} isActive={isActive} />
        <NavSection label="Library" items={NAV_LIBRARY} isActive={isActive} />
      </nav>

      <div className="mt-3 space-y-3 rounded-[22px] border border-[var(--color-aria-border)] bg-white/4 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-aria-muted)]">
              Plan usage
            </p>
            <p className="mt-1 text-sm font-semibold text-[var(--color-aria-ink)]">Pro plan active</p>
          </div>
          <span className="rounded-full bg-[var(--color-aria-blue-dim)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-[var(--color-aria-blue)]">
            68%
          </span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-white/8">
          <div className="gradient-btn h-full w-[68%] rounded-full" />
        </div>
        <div className="flex items-center justify-between text-xs text-[var(--color-aria-muted)]">
          <span>Resets in 7 days</span>
          <button className="inline-flex items-center gap-1 font-medium text-[var(--color-aria-ink)] transition-opacity hover:opacity-75">
            <Settings className="h-3.5 w-3.5" />
            Settings
          </button>
        </div>
      </div>
    </aside>
  );
}

function NavSection({
  label,
  items,
  isActive,
}: {
  label: string;
  items: typeof NAV_MAIN;
  isActive: (path: string) => boolean;
}) {
  return (
    <div>
      <p className="px-3 text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-aria-faint)]">
        {label}
      </p>
      <div className="mt-2 space-y-1">
        {items.map((item) => {
          const active = isActive(item.path);
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                "group flex items-center gap-3 rounded-2xl px-3 py-3 text-sm transition-all duration-150",
                active
                  ? "bg-white/10 text-[var(--color-aria-ink)] shadow-[inset_0_0_0_1px_rgba(148,163,184,0.18)]"
                  : "text-[var(--color-aria-muted)] hover:bg-white/6 hover:text-[var(--color-aria-ink)]"
              )}
            >
              <div
                className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-xl border transition-colors",
                  active
                    ? "border-[var(--color-aria-blue)]/30 bg-[var(--color-aria-blue-dim)] text-[var(--color-aria-blue)]"
                    : "border-[var(--color-aria-border)] bg-white/4 text-[var(--color-aria-muted)] group-hover:text-[var(--color-aria-ink)]"
                )}
              >
                <item.icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium">{item.label}</p>
              </div>
              <div
                className={cn(
                  "h-2 w-2 rounded-full transition-opacity",
                  active ? "bg-[var(--color-aria-cyan)] opacity-100" : "bg-transparent opacity-0"
                )}
              />
            </NavLink>
          );
        })}
      </div>
    </div>
  );
}

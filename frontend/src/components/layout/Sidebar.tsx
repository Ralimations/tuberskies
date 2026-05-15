import {
  LayoutDashboard,
  Sparkles,
  BarChart2,
  Upload,
  Vault,
  BookOpen,
  Music2,
} from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

const NAV_PRIMARY = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard, hint: "Daily priorities" },
  { label: "Create", path: "/create", icon: Sparkles, hint: "Ideas and packaging" },
  { label: "Analyze", path: "/analyze", icon: BarChart2, hint: "Performance review" },
  { label: "Publish", path: "/publish", icon: Upload, hint: "Release workflow" },
  { label: "Vault", path: "/vault", icon: Vault, hint: "Connections and settings" },
];

const NAV_SECONDARY = [
  { label: "Learn", path: "/learn", icon: BookOpen },
  { label: "Repertoire", path: "/repertoire", icon: Music2 },
];

export function Sidebar() {
  const location = useLocation();

  function isActive(path: string) {
    return path === "/" ? location.pathname === "/" : location.pathname.startsWith(path);
  }

  return (
    <aside className="glass-panel rounded-[28px] border border-[var(--color-aria-border)] p-5 shadow-[0_18px_60px_rgba(2,8,23,0.28)]">
      <div className="rounded-[22px] border border-[var(--color-aria-border)] bg-white/4 p-6">
        <div className="flex items-center gap-3">
          <div className="gradient-btn flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl">
            <span className="font-mono text-sm font-black text-slate-950">A</span>
          </div>
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[var(--color-aria-muted)]">A.R.I.A.</p>
            <p className="text-lg font-semibold text-[var(--color-aria-ink)]">Creator strategist</p>
          </div>
        </div>
        <p className="mt-4 text-sm leading-6 text-[var(--color-aria-muted)]">
          Start with the next decision. Everything else is support.
        </p>
      </div>

      <nav className="space-y-6 px-1 py-6">
        <div>
          <p className="px-4 text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-aria-faint)]">
            Core workflow
          </p>
          <div className="mt-3 space-y-3">
            {NAV_PRIMARY.map((item) => {
              const active = isActive(item.path);
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "group flex items-center gap-3 rounded-2xl px-4 py-4 transition-all duration-150",
                    active
                      ? "bg-white/10 text-[var(--color-aria-ink)] shadow-[inset_0_0_0_1px_rgba(148,163,184,0.18)]"
                      : "text-[var(--color-aria-muted)] hover:bg-white/6 hover:text-[var(--color-aria-ink)]",
                  )}
                >
                  <div
                    className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-xl border transition-colors",
                      active
                        ? "border-[var(--color-aria-blue)]/30 bg-[var(--color-aria-blue-dim)] text-[var(--color-aria-blue)]"
                        : "border-[var(--color-aria-border)] bg-white/4 text-[var(--color-aria-muted)] group-hover:text-[var(--color-aria-ink)]",
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{item.label}</p>
                    <p className="text-xs text-[var(--color-aria-faint)]">{item.hint}</p>
                  </div>
                </NavLink>
              );
            })}
          </div>
        </div>

        <div className="border-t border-[var(--color-aria-border)] pt-6">
          <p className="px-4 text-[10px] font-semibold uppercase tracking-[0.24em] text-[var(--color-aria-faint)]">
            Reference
          </p>
          <div className="mt-3 space-y-3">
            {NAV_SECONDARY.map((item) => {
              const active = isActive(item.path);
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "flex items-center gap-3 rounded-2xl px-4 py-4 text-sm transition-colors",
                    active
                      ? "bg-white/8 text-[var(--color-aria-ink)]"
                      : "text-[var(--color-aria-muted)] hover:bg-white/6 hover:text-[var(--color-aria-ink)]",
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </div>
        </div>
      </nav>

      <div className="mt-4 rounded-[22px] border border-[var(--color-aria-border)] bg-white/4 p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--color-aria-muted)]">Plan usage</p>
            <p className="mt-2 text-sm font-semibold text-[var(--color-aria-ink)]">Pro plan active</p>
          </div>
          <span className="text-sm font-semibold text-[var(--color-aria-blue)]">68%</span>
        </div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/8">
          <div className="gradient-btn h-full w-[68%] rounded-full" />
        </div>
        <p className="mt-4 text-xs text-[var(--color-aria-muted)]">Enough room for this week. Reset in 7 days.</p>
      </div>
    </aside>
  );
}

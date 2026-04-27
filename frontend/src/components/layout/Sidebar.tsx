import {
  LayoutDashboard,
  Sparkles,
  Zap,
  Upload,
  BarChart2,
  BookOpen,
  Music2,
  Vault,
  ChevronDown,
  Settings,
  Sun,
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
    <aside className="fixed inset-y-0 left-0 z-40 flex w-[220px] flex-col border-r border-[var(--color-aria-border)] bg-[var(--color-aria-surface)]">
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-[var(--color-aria-border)]">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg gradient-btn shadow-md shrink-0">
          <span className="text-white font-black text-sm font-mono">A</span>
        </div>
        <div>
          <p className="text-sm font-bold text-[var(--color-aria-ink)] leading-none">A.R.I.A.</p>
          <p className="text-[10px] text-[var(--color-aria-muted)] uppercase tracking-widest mt-0.5">AI Creator System</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        <NavSection label="Main" items={NAV_MAIN} isActive={isActive} />
        <NavSection label="Library" items={NAV_LIBRARY} isActive={isActive} />
      </nav>

      {/* User */}
      <div className="border-t border-[var(--color-aria-border)] px-3 py-3 space-y-2">
        {/* Plan badge */}
        <div className="px-3 py-2 rounded-lg bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)]">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-semibold text-[var(--color-aria-ink)]">Pro Plan</span>
            <span className="text-[10px] text-[var(--color-aria-muted)]">Resets in 7 days</span>
          </div>
          <div className="h-1 rounded-full bg-[var(--color-aria-faint)]">
            <div className="h-full w-[68%] rounded-full gradient-btn" />
          </div>
          <p className="text-[10px] text-[var(--color-aria-muted)] mt-1">68% used</p>
        </div>

        {/* Profile row */}
        <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-[var(--color-aria-surface-3)] cursor-pointer transition-colors">
          <div className="h-7 w-7 rounded-full gradient-btn flex items-center justify-center shrink-0">
            <span className="text-white text-xs font-bold">R</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-[var(--color-aria-ink)] truncate">Ralskies</p>
            <p className="text-[10px] text-[var(--color-aria-muted)] truncate">Creator</p>
          </div>
          <ChevronDown className="h-3.5 w-3.5 text-[var(--color-aria-muted)] shrink-0" />
        </div>

        {/* Bottom icons */}
        <div className="flex gap-1 px-1">
          <button className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--color-aria-muted)] hover:text-[var(--color-aria-ink)] hover:bg-[var(--color-aria-surface-3)] transition-colors">
            <Sun className="h-4 w-4" />
          </button>
          <button className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--color-aria-muted)] hover:text-[var(--color-aria-ink)] hover:bg-[var(--color-aria-surface-3)] transition-colors">
            <Settings className="h-4 w-4" />
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
      <p className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-faint)]">
        {label}
      </p>
      <div className="space-y-0.5">
        {items.map((item) => {
          const active = isActive(item.path);
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150",
                active
                  ? "bg-[var(--color-aria-blue-dim)] text-[var(--color-aria-blue)] shadow-sm"
                  : "text-[var(--color-aria-muted)] hover:text-[var(--color-aria-ink)] hover:bg-[var(--color-aria-surface-3)]"
              )}
            >
              <item.icon
                className={cn(
                  "h-4 w-4 shrink-0",
                  active ? "text-[var(--color-aria-blue)]" : "text-[var(--color-aria-muted)]"
                )}
              />
              {item.label}
              {active && (
                <div className="ml-auto h-1.5 w-1.5 rounded-full bg-[var(--color-aria-blue)]" />
              )}
            </NavLink>
          );
        })}
      </div>
    </div>
  );
}

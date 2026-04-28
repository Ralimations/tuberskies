import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { ARIAPanel } from "./ARIAPanel";
import { BootstrapProvider } from "@/context/BootstrapContext";

export function AppShell() {
  return (
    <BootstrapProvider>
      <div className="min-h-screen bg-[var(--color-aria-bg)] text-[var(--color-aria-ink)]">
        <div className="mx-auto flex min-h-screen max-w-[1720px] flex-col gap-4 px-3 py-3 lg:grid lg:grid-cols-[272px_minmax(0,1fr)] xl:grid-cols-[272px_minmax(0,1fr)_360px] xl:px-5 xl:py-5">
          <Sidebar />
          <main className="glass-panel min-w-0 rounded-[28px] border border-[var(--color-aria-border)] shadow-[0_24px_80px_rgba(2,8,23,0.34)]">
            <div className="min-h-full px-4 py-5 sm:px-6 lg:px-8 lg:py-8">
              <Outlet />
            </div>
          </main>
          <ARIAPanel />
        </div>
      </div>
    </BootstrapProvider>
  );
}

import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { ARIAPanel } from "./ARIAPanel";
import { BootstrapProvider } from "@/context/BootstrapContext";

export function AppShell() {
  return (
    <BootstrapProvider>
      <div className="min-h-screen bg-[var(--color-aria-bg)] text-[var(--color-aria-ink)]">
        <div className="mx-auto flex min-h-screen max-w-[1760px] flex-col gap-6 px-8 py-6 lg:grid lg:grid-cols-[256px_minmax(0,1fr)] 2xl:grid-cols-[256px_minmax(0,1fr)_320px] 2xl:px-10">
          <Sidebar />
          <main className="glass-panel min-w-0 rounded-[28px] border border-[var(--color-aria-border)] shadow-[0_24px_80px_rgba(2,8,23,0.34)]">
            <div className="min-h-full px-10 py-8">
              <Outlet />
            </div>
          </main>
          <ARIAPanel />
        </div>
      </div>
    </BootstrapProvider>
  );
}

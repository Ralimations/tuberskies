import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { ARIAPanel } from "./ARIAPanel";

export function AppShell() {
  return (
    <div className="flex min-h-screen bg-[var(--color-aria-bg)]">
      <Sidebar />
      {/* Main content — offset by sidebar (220px) and right panel (280px) */}
      <main className="flex-1 ml-[220px] mr-[280px] min-h-screen">
        <div className="max-w-[960px] mx-auto px-8 py-8">
          <Outlet />
        </div>
      </main>
      <ARIAPanel />
    </div>
  );
}

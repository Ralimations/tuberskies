import { Suspense, lazy } from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";

const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Create = lazy(() => import("@/pages/Create"));
const Optimize = lazy(() => import("@/pages/Optimize"));
const Publish = lazy(() => import("@/pages/Publish"));
const Analyze = lazy(() => import("@/pages/Analyze"));
const Learn = lazy(() => import("@/pages/Learn"));
const Repertoire = lazy(() => import("@/pages/Repertoire"));
const Vault = lazy(() => import("@/pages/Vault"));

function RouteLoadingFallback() {
  return (
    <div className="flex h-[60vh] items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="gradient-btn h-8 w-8 animate-pulse rounded-full" />
        <p className="text-sm text-[var(--color-aria-muted)]">Loading workspace...</p>
      </div>
    </div>
  );
}

function withSuspense(element: React.ReactNode) {
  return <Suspense fallback={<RouteLoadingFallback />}>{element}</Suspense>;
}

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      {
        index: true,
        element: withSuspense(<Dashboard />),
      },
      {
        path: "create",
        element: withSuspense(<Create />),
      },
      {
        path: "optimize",
        element: withSuspense(<Optimize />),
      },
      {
        path: "publish",
        element: withSuspense(<Publish />),
      },
      {
        path: "analyze",
        element: withSuspense(<Analyze />),
      },
      {
        path: "learn",
        element: withSuspense(<Learn />),
      },
      {
        path: "repertoire",
        element: withSuspense(<Repertoire />),
      },
      {
        path: "vault",
        element: withSuspense(<Vault />),
      },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}

import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";

// Pages
import Dashboard from "@/pages/Dashboard";
import Create from "@/pages/Create";
import Optimize from "@/pages/Optimize";
import Publish from "@/pages/Publish";
import Analyze from "@/pages/Analyze";
import Learn from "@/pages/Learn";
import Repertoire from "@/pages/Repertoire";
import Vault from "@/pages/Vault";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: "create",
        element: <Create />,
      },
      {
        path: "optimize",
        element: <Optimize />,
      },
      {
        path: "publish",
        element: <Publish />,
      },
      {
        path: "analyze",
        element: <Analyze />,
      },
      {
        path: "learn",
        element: <Learn />,
      },
      {
        path: "repertoire",
        element: <Repertoire />,
      },
      {
        path: "vault",
        element: <Vault />,
      },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}

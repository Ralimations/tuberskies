import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { loadBootstrap } from "@/api";
import type { BootstrapPayload } from "@/types";

interface BootstrapContextValue {
  data: BootstrapPayload | null;
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

const BootstrapContext = createContext<BootstrapContextValue>({
  data: null,
  loading: true,
  error: null,
  refresh: async () => {},
});

export function BootstrapProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<BootstrapPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const payload = await loadBootstrap();
      setData(payload);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Bootstrap refresh failed."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <BootstrapContext.Provider value={{ data, loading, error, refresh }}>
      {children}
    </BootstrapContext.Provider>
  );
}

export function useBootstrap() {
  return useContext(BootstrapContext);
}

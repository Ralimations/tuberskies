import { useEffect, useState } from "react";
import { Shield, Link2, RefreshCw, Trash2, Save } from "lucide-react";
import { motion } from "framer-motion";
import { loadVault, saveVault, authorizeYoutube, clearYoutubeToken, checkLatestYoutubeData } from "@/api";
import type { VaultPayload } from "@/types";
import { PageHeader } from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { DataTable } from "@/components/shared/DataTable";
import { useBootstrap } from "@/context/BootstrapContext";

export default function Vault() {
  const { refresh } = useBootstrap();
  const [payload, setPayload] = useState<VaultPayload | null>(null);
  const [settings, setSettings] = useState<VaultPayload["settings"] | null>(null);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    loadVault()
      .then((result) => {
        setPayload(result);
        setSettings(result.settings);
      })
      .catch((e: Error) => setStatus(e.message));
  }, []);

  function update(key: keyof VaultPayload["settings"], value: string) {
    if (!settings) return;
    setSettings({ ...settings, [key]: value });
  }

  async function save() {
    if (!settings) return;
    setBusy(true);
    try {
      const result = await saveVault(settings);
      setPayload(result);
      setSettings(result.settings);
      setStatus("Vault settings saved.");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Save failed.");
    } finally {
      setBusy(false);
    }
  }

  async function reconnect() {
    setBusy(true);
    try {
      const result = await authorizeYoutube();
      setPayload(result);
      setStatus(result.message ?? result.connection.message);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Auth failed.");
    } finally {
      setBusy(false);
    }
  }

  async function clearToken() {
    setBusy(true);
    try {
      const result = await clearYoutubeToken();
      setPayload(result);
      setStatus(result.message ?? "Token cleared.");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Failed.");
    } finally {
      setBusy(false);
    }
  }

  async function checkLatest() {
    setBusy(true);
    setStatus("Checking latest YouTube data...");
    try {
      const result = await checkLatestYoutubeData();
      setStatus(Object.entries(result.messages).map(([k, v]) => `${k}: ${v}`).join("\n") || "Done.");
      const freshVault = await loadVault();
      setPayload(freshVault);
      setSettings(freshVault.settings);
      await refresh();
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Check failed.");
    } finally {
      setBusy(false);
    }
  }

  const conn = payload?.connection;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-[var(--space-section)]">
      <PageHeader title="The Vault" subtitle="API keys, YouTube credentials, model settings, and creator profile." />

      {status && (
        <div className="rounded-xl border border-[var(--color-aria-blue)]/20 bg-[var(--color-aria-blue-dim)] px-4 py-3 text-sm text-[var(--color-aria-blue)] whitespace-pre-wrap">
          {status}
        </div>
      )}

      <div className="grid grid-cols-1 gap-[var(--space-card-grid)] md:grid-cols-12">
        <div className="md:col-span-4">
          <ConnCard label="API Key" ok={conn?.api_key} sub="YouTube Data API" />
        </div>
        <div className="md:col-span-4">
          <ConnCard label="OAuth Client" ok={conn?.oauth_client} sub="Write access" />
        </div>
        <div className="md:col-span-4">
          <ConnCard label="Token" ok={conn?.token} sub="Saved locally" />
        </div>
      </div>

      <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6">
        <div className="mb-[var(--space-default)] flex items-center gap-[var(--space-tight)]">
          <Link2 className="h-4 w-4 text-[var(--color-aria-blue)]" />
          <p className="text-sm font-semibold text-[var(--color-aria-ink)]">YouTube Connection</p>
          {conn && <Badge color={conn.connected ? "green" : "amber"} dot>{conn.message}</Badge>}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" size="sm" onClick={reconnect} disabled={busy || !conn?.oauth_client}>
            <Link2 className="h-3.5 w-3.5" /> Reconnect
          </Button>
          <Button variant="secondary" size="sm" onClick={checkLatest} disabled={busy || !conn?.token}>
            <RefreshCw className="h-3.5 w-3.5" /> Check Latest Data
          </Button>
          <Button variant="danger" size="sm" onClick={clearToken} disabled={busy || !conn?.token}>
            <Trash2 className="h-3.5 w-3.5" /> Clear Token
          </Button>
        </div>
      </div>

      {settings && (
        <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6 space-y-[var(--space-section)]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-[var(--color-aria-muted)]" />
              <p className="text-sm font-semibold text-[var(--color-aria-ink)]">Settings</p>
            </div>
            <Button variant="primary" size="sm" onClick={save} disabled={busy}>
              <Save className="h-3.5 w-3.5" /> Save Changes
            </Button>
          </div>

          <div className="grid grid-cols-1 gap-[var(--space-card-grid)] md:grid-cols-2">
            <Field label="Model Name" value={settings.model_name} onChange={(v) => update("model_name", v)} />
            <Field label="Model Endpoint" value={settings.model_endpoint} onChange={(v) => update("model_endpoint", v)} />
            <Field label="YouTube API Key" value={settings.youtube_api_key} onChange={(v) => update("youtube_api_key", v)} secret />
            <Field label="YouTube Client ID" value={settings.youtube_client_id} onChange={(v) => update("youtube_client_id", v)} secret />
            <Field label="YouTube Client Secret" value={settings.youtube_client_secret} onChange={(v) => update("youtube_client_secret", v)} secret />
          </div>

          <div className="border-t border-[var(--color-aria-border)] pt-2">
            <p className="mb-[var(--space-default)] text-xs font-semibold uppercase tracking-widest text-[var(--color-aria-muted)]">Creator Profile</p>
            <div className="grid grid-cols-1 gap-[var(--space-card-grid)] md:grid-cols-2">
              <Field label="Channel Name" value={settings.channel_name} onChange={(v) => update("channel_name", v)} />
              <Field label="Niche" value={settings.niche} onChange={(v) => update("niche", v)} />
              <Field label="Target Audience" value={settings.target_audience} onChange={(v) => update("target_audience", v)} />
              <Field label="Tone" value={settings.tone} onChange={(v) => update("tone", v)} />
            </div>
            <div className="mt-[var(--space-default)]">
              <label className="mb-2 block text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-muted)]">
                Default Description
              </label>
              <textarea
                value={settings.default_description}
                onChange={(e) => update("default_description", e.target.value)}
                rows={6}
                className="w-full resize-none rounded-xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface-3)] px-4 py-3 font-mono text-sm text-[var(--color-aria-ink)] outline-none transition-colors focus:border-[var(--color-aria-blue)]"
              />
            </div>
          </div>
        </div>
      )}

      {payload?.cache?.length ? (
        <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6">
          <p className="mb-[var(--space-default)] text-sm font-semibold text-[var(--color-aria-ink)]">Data Freshness</p>
          <DataTable rows={payload.cache} columns={["dataset", "status", "latest_data_date", "today_date"]} />
        </div>
      ) : null}
    </motion.div>
  );
}

function ConnCard({ label, ok, sub }: { label: string; ok?: boolean; sub: string }) {
  return (
    <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-6 text-center">
      <p className="mb-1 text-xs text-[var(--color-aria-muted)]">{label}</p>
      <p className={`font-mono text-xl font-black ${ok ? "text-[var(--color-aria-green)]" : "text-[var(--color-aria-red)]"}`}>
        {ok ? "Yes" : "No"}
      </p>
      <p className="mt-2 text-[10px] text-[var(--color-aria-faint)]">{sub}</p>
    </div>
  );
}

function Field({ label, value, onChange, secret }: { label: string; value: string; onChange: (v: string) => void; secret?: boolean }) {
  return (
    <div>
      <label className="mb-2 block text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-muted)]">{label}</label>
      <input
        type={secret ? "password" : "text"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface-3)] px-4 py-3 font-mono text-sm text-[var(--color-aria-ink)] outline-none transition-colors focus:border-[var(--color-aria-blue)]"
      />
    </div>
  );
}

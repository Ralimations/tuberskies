import { useEffect, useState } from "react";
import { Shield, Link2, RefreshCw, Trash2, Save } from "lucide-react";
import { motion } from "framer-motion";
import { loadVault, saveVault, authorizeYoutube, clearYoutubeToken, checkLatestYoutubeData } from "@/api";
import type { VaultPayload } from "@/types";
import { PageHeader } from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { DataTable } from "@/components/shared/DataTable";

export default function Vault() {
  const [payload, setPayload] = useState<VaultPayload | null>(null);
  const [settings, setSettings] = useState<VaultPayload["settings"] | null>(null);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    loadVault().then((r) => { setPayload(r); setSettings(r.settings); }).catch((e: Error) => setStatus(e.message));
  }, []);

  function update(key: keyof VaultPayload["settings"], value: string) {
    if (!settings) return;
    setSettings({ ...settings, [key]: value });
  }

  async function save() {
    if (!settings) return;
    setBusy(true);
    try {
      const r = await saveVault(settings);
      setPayload(r);
      setSettings(r.settings);
      setStatus("Vault settings saved.");
    } catch (e) { setStatus(e instanceof Error ? e.message : "Save failed."); }
    finally { setBusy(false); }
  }

  async function reconnect() {
    setBusy(true);
    try {
      const r = await authorizeYoutube();
      setPayload(r);
      setStatus(r.message ?? r.connection.message);
    } catch (e) { setStatus(e instanceof Error ? e.message : "Auth failed."); }
    finally { setBusy(false); }
  }

  async function clearToken() {
    setBusy(true);
    try {
      const r = await clearYoutubeToken();
      setPayload(r);
      setStatus(r.message ?? "Token cleared.");
    } catch (e) { setStatus(e instanceof Error ? e.message : "Failed."); }
    finally { setBusy(false); }
  }

  async function checkLatest() {
    setBusy(true);
    setStatus("Checking latest YouTube data…");
    try {
      const r = await checkLatestYoutubeData();
      setStatus(Object.entries(r.messages).map(([k, v]) => `${k}: ${v}`).join("\n") || "Done.");
      setPayload((prev) => prev ? { ...prev, cache: r.cache } : prev);
    } catch (e) { setStatus(e instanceof Error ? e.message : "Check failed."); }
    finally { setBusy(false); }
  }

  const conn = payload?.connection;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      <PageHeader title="The Vault" subtitle="API keys, YouTube credentials, model settings, and creator profile." />

      {status && (
        <div className="rounded-xl border border-[var(--color-aria-blue)]/20 bg-[var(--color-aria-blue-dim)] px-4 py-3 text-sm text-[var(--color-aria-blue)] whitespace-pre-wrap">{status}</div>
      )}

      {/* Connection status cards */}
      <div className="grid grid-cols-3 gap-3">
        <ConnCard label="API Key" ok={conn?.api_key} sub="YouTube Data API" />
        <ConnCard label="OAuth Client" ok={conn?.oauth_client} sub="Write access" />
        <ConnCard label="Token" ok={conn?.token} sub="Saved locally" />
      </div>

      {/* YouTube actions */}
      <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5">
        <div className="flex items-center gap-2 mb-4">
          <Link2 className="h-4 w-4 text-[var(--color-aria-blue)]" />
          <p className="text-sm font-semibold text-[var(--color-aria-ink)]">YouTube Connection</p>
          {conn && <Badge color={conn.connected ? "green" : "amber"} dot>{conn.message}</Badge>}
        </div>
        <div className="flex gap-2 flex-wrap">
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

      {/* Settings form */}
      {settings && (
        <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5 space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-[var(--color-aria-muted)]" />
              <p className="text-sm font-semibold text-[var(--color-aria-ink)]">Settings</p>
            </div>
            <Button variant="primary" size="sm" onClick={save} disabled={busy}>
              <Save className="h-3.5 w-3.5" /> Save Changes
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Model Name" value={settings.model_name} onChange={(v) => update("model_name", v)} />
            <Field label="Model Endpoint" value={settings.model_endpoint} onChange={(v) => update("model_endpoint", v)} />
            <Field label="YouTube API Key" value={settings.youtube_api_key} onChange={(v) => update("youtube_api_key", v)} secret />
            <Field label="YouTube Client ID" value={settings.youtube_client_id} onChange={(v) => update("youtube_client_id", v)} secret />
            <Field label="YouTube Client Secret" value={settings.youtube_client_secret} onChange={(v) => update("youtube_client_secret", v)} secret />
          </div>

          <div className="pt-2 border-t border-[var(--color-aria-border)]">
            <p className="text-xs font-semibold uppercase tracking-widest text-[var(--color-aria-muted)] mb-4">Creator Profile</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label="Channel Name" value={settings.channel_name} onChange={(v) => update("channel_name", v)} />
              <Field label="Niche" value={settings.niche} onChange={(v) => update("niche", v)} />
              <Field label="Target Audience" value={settings.target_audience} onChange={(v) => update("target_audience", v)} />
              <Field label="Tone" value={settings.tone} onChange={(v) => update("tone", v)} />
            </div>
            <div className="mt-4">
              <label className="block text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-muted)] mb-1.5">Default Description</label>
              <textarea value={settings.default_description} onChange={(e) => update("default_description", e.target.value)} rows={6}
                className="w-full bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] rounded-xl px-4 py-3 text-sm text-[var(--color-aria-ink)] outline-none focus:border-[var(--color-aria-blue)] transition-colors resize-none font-mono" />
            </div>
          </div>
        </div>
      )}

      {/* Data freshness */}
      {payload?.cache?.length ? (
        <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-5">
          <p className="text-sm font-semibold text-[var(--color-aria-ink)] mb-4">Data Freshness</p>
          <DataTable rows={payload.cache} columns={["dataset","status","latest_data_date","today_date"]} />
        </div>
      ) : null}
    </motion.div>
  );
}

function ConnCard({ label, ok, sub }: { label: string; ok?: boolean; sub: string }) {
  return (
    <div className="rounded-2xl border border-[var(--color-aria-border)] bg-[var(--color-aria-surface)] p-4 text-center">
      <p className="text-xs text-[var(--color-aria-muted)] mb-1">{label}</p>
      <p className={`text-xl font-black font-mono ${ok ? "text-[var(--color-aria-green)]" : "text-[var(--color-aria-red)]"}`}>{ok ? "Yes" : "No"}</p>
      <p className="text-[10px] text-[var(--color-aria-faint)] mt-1">{sub}</p>
    </div>
  );
}

function Field({ label, value, onChange, secret }: { label: string; value: string; onChange: (v: string) => void; secret?: boolean }) {
  return (
    <div>
      <label className="block text-[10px] font-semibold uppercase tracking-widest text-[var(--color-aria-muted)] mb-1.5">{label}</label>
      <input type={secret ? "password" : "text"} value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full bg-[var(--color-aria-surface-3)] border border-[var(--color-aria-border)] rounded-xl px-4 py-2.5 text-sm text-[var(--color-aria-ink)] outline-none focus:border-[var(--color-aria-blue)] transition-colors font-mono" />
    </div>
  );
}

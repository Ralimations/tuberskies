import type { AnalyticsPayload, BootstrapPayload, ChatMessage, CreatorActionsPayload, IdeationScorePayload, VaultPayload, YoutubeRefreshPayload } from "./types";

export async function loadBootstrap(): Promise<BootstrapPayload> {
  const response = await fetch("/api/bootstrap");
  if (!response.ok) {
    throw new Error(`Bootstrap failed: ${response.status}`);
  }
  return response.json();
}

export async function askAria(message: string, history: ChatMessage[]): Promise<ChatMessage> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history })
  });
  if (!response.ok) {
    throw new Error(`A.R.I.A. request failed: ${response.status}`);
  }
  return response.json();
}

export async function askAriaStream(message: string, history: ChatMessage[], onChunk: (chunk: string) => void): Promise<void> {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history })
  });
  if (!response.ok || !response.body) {
    throw new Error(`A.R.I.A. stream failed: ${response.status}`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    onChunk(decoder.decode(value, { stream: true }));
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    let detail = "";
    try {
      const payload = await response.json();
      detail = String(payload.detail ?? payload.message ?? "");
    } catch {
      detail = await response.text().catch(() => "");
    }
    throw new Error(`${path} failed: ${response.status}${detail ? ` - ${detail}` : ""}`);
  }
  return response.json();
}

export function loadVault(): Promise<VaultPayload> {
  return requestJson("/api/vault");
}

export function saveVault(settings: VaultPayload["settings"]): Promise<VaultPayload> {
  return requestJson("/api/vault", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings)
  });
}

export function clearYoutubeToken(): Promise<VaultPayload & { message?: string }> {
  return requestJson("/api/vault/youtube/clear-token", { method: "POST" });
}

export function authorizeYoutube(): Promise<VaultPayload & { message?: string }> {
  return requestJson("/api/vault/youtube/authorize", { method: "POST" });
}

export function checkLatestYoutubeData(): Promise<YoutubeRefreshPayload> {
  return requestJson("/api/vault/youtube/check-latest", { method: "POST" });
}



export function loadCreatorActions(): Promise<CreatorActionsPayload> {
  return requestJson("/api/creator-actions");
}

export function loadMetadata(videoId: string): Promise<{ metadata: Record<string, unknown> | null; message: string }> {
  return requestJson("/api/creator-actions/metadata/load", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_id: videoId })
  });
}

export function draftMetadata(videoLabel: string, reason = "", currentTitle = ""): Promise<{ content: string }> {
  return requestJson("/api/creator-actions/metadata/draft", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_label: videoLabel, reason, current_title: currentTitle })
  });
}

export function publishMetadata(payload: { video_id: string; title: string; description: string; tags: string[]; reviewed: boolean }): Promise<{ success: boolean; message: string }> {
  return requestJson("/api/creator-actions/metadata/publish", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export function generateIdeation(payload: { topic: string; working_title: string; action: string; fan_request?: string }): Promise<{ content: string }> {
  return requestJson("/api/ideation/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export function scoreIdeation(topic: string, workingTitle: string): Promise<IdeationScorePayload> {
  return requestJson("/api/ideation/score", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic, working_title: workingTitle })
  });
}

export function loadAnalytics(): Promise<AnalyticsPayload> {
  return requestJson("/api/analytics");
}

export function draftUploadTips(upload: Record<string, unknown>, uploadKind: string): Promise<{ content: string }> {
  return requestJson("/api/upload-lab/tips", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ upload, upload_kind: uploadKind })
  });
}



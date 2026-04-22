import type { BootstrapPayload, ChatMessage, CommentRow, CreatorActionsPayload, RepertoirePayload, VaultPayload } from "./types";

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

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    throw new Error(`${path} failed: ${response.status}`);
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

export function loadRepertoire(): Promise<RepertoirePayload> {
  return requestJson("/api/repertoire");
}

export function saveRepertoire(rows: Record<string, unknown>[]): Promise<RepertoirePayload> {
  return requestJson("/api/repertoire", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rows })
  });
}

export function coachRepertoire(prompt: string): Promise<{ content: string }> {
  return requestJson("/api/repertoire/coach", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt })
  });
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

export function draftMetadata(videoLabel: string): Promise<{ content: string }> {
  return requestJson("/api/creator-actions/metadata/draft", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_label: videoLabel })
  });
}

export function publishMetadata(payload: { video_id: string; title: string; description: string; tags: string[]; reviewed: boolean }): Promise<{ success: boolean; message: string }> {
  return requestJson("/api/creator-actions/metadata/publish", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export function loadComments(videoId: string): Promise<{ rows: CommentRow[]; message: string }> {
  return requestJson("/api/creator-actions/comments/list", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_id: videoId })
  });
}

export function draftComment(author: string, text: string): Promise<{ content: string }> {
  return requestJson("/api/creator-actions/comments/draft", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ author, text })
  });
}

export function publishComment(payload: { comment_id: string; reply_text: string; reviewed: boolean }): Promise<{ success: boolean; message: string }> {
  return requestJson("/api/creator-actions/comments/publish", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export type NavItem = {
  label: string;
  path: string;
  icon: string;
  group: string;
};

export type Stat = {
  label: string;
  value: string;
  meta: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type BootstrapPayload = {
  navigation: NavItem[];
  chatSuggestions: string[];
  profile: {
    title: string;
    handle: string;
    source: string;
  };
  stats: Stat[];
  today: {
    focus_title: string;
    focus_reason: string;
    risk_title: string;
    risk_reason: string;
    opportunity_title: string;
    opportunity_reason: string;
    today_action: string;
  };
  uploadTakeaways: {
    best?: Record<string, unknown> | null;
    weak?: Record<string, unknown> | null;
    pattern_rows?: [string, string][];
    improvement_rows?: [string, string][];
  };
  patternMemory: Record<string, unknown> | null;
  analyticsRows: Record<string, unknown>[];
  videoRows: Record<string, unknown>[];
  calendarRows: Record<string, unknown>[];
  messages: Record<string, string>;
};

export type RepertoirePayload = {
  rows: Record<string, unknown>[];
  stages: string[];
  priorities: string[];
  summary: {
    total: number;
    ready: number;
    due_soon: number;
    stage_counts: Record<string, number>;
  };
};

export type VaultPayload = {
  settings: {
    default_description: string;
    youtube_api_key: string;
    youtube_client_id: string;
    youtube_client_secret: string;
    ollama_model: string;
  };
  connection: {
    api_key: boolean;
    oauth_client: boolean;
    token: boolean;
  };
};

export type CreatorActionsPayload = {
  videos: { label: string; video_id: string; title: string }[];
  message: string;
  guardrails: [string, string][];
};

export type CommentRow = {
  author?: string;
  text?: string;
  comment_id?: string;
  video_id?: string;
  can_reply?: boolean;
  already_replied?: boolean;
  reply_count?: number;
};

export type IdeationScorePayload = {
  keywords: Record<string, unknown>[];
  scorecard: { label: string; value: string }[];
};

export type AnalyticsPayload = {
  source: string;
  profile: {
    title?: string;
    handle?: string;
  };
  stats: Stat[];
  today: BootstrapPayload["today"];
  rows: Record<string, unknown>[];
  alerts: Record<string, unknown>[];
  publishTiming: Record<string, unknown>[];
  auditRows: { label: string; value: string }[];
  actionCards: {
    category: string;
    title: string;
    body: string;
    cta: string;
    path: string;
  }[];
  messages: Record<string, string>;
};

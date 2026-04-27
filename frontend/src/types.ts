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
  messages: Record<string, string>;
  cache: CacheFreshnessRow[];
};

export type CacheFreshnessRow = {
  dataset: string;
  cache_key: string;
  status: string;
  today_date: string;
  latest_data_date: string;
  payload_kind: string;
  updated_at: string;
  message: string;
};



export type VaultPayload = {
  settings: {
    default_description: string;
    youtube_api_key: string;
    youtube_client_id: string;
    youtube_client_secret: string;
    model_name: string;
    model_endpoint: string;
  };
  available_models: string[];
  recommended_free_vision_models: { name: string; label: string }[];
  connection: {
    api_key: boolean;
    oauth_client: boolean;
    token: boolean;
    connected: boolean;
    message: string;
  };
  cache: CacheFreshnessRow[];
};

export type YoutubeRefreshPayload = {
  success: boolean;
  messages: Record<string, string>;
  profile?: Record<string, unknown> | null;
  cache: VaultPayload["cache"];
};

export type CreatorActionsPayload = {
  videos: { label: string; video_id: string; title: string }[];
  metadataActions: {
    video_id: string;
    title: string;
    label: string;
    views: number;
    retention: number;
    watch_time_hours: number;
    engagement_score: number;
    reason: string;
    suggestion: string;
  }[];
  message: string;
  guardrails: [string, string][];
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



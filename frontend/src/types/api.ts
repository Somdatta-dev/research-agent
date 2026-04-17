export type Uuid = string;
export type IsoDateTime = string;

export interface Recipient {
  email: string;
  name?: string | null;
}

export interface SearchConfig {
  providers: string[];
  max_results_per_query: number;
  recency_days: number;
}

export interface LLMTierOverride {
  base_url?: string | null;
  api_key?: string | null;
  model?: string | null;
  temperature?: number | null;
  max_tokens?: number | null;
  timeout_s?: number | null;
}

export interface LLMConfig {
  primary: LLMTierOverride;
  fast: LLMTierOverride;
}

export interface ReportConfigBase {
  name: string;
  topic: string;
  focus_areas: string[];
  schedule_cron: string;
  timezone: string;
  recipients: Recipient[];
  search_config: SearchConfig;
  llm_config: LLMConfig;
  dedup_window_days: number;
  pdf_template: string;
  max_pages: number;
  active: boolean;
}

export interface ReportConfig extends ReportConfigBase {
  id: Uuid;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
}

export type ReportConfigCreate = ReportConfigBase;
export type ReportConfigUpdate = Partial<ReportConfigBase>;

export type RunStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";
export type RunTrigger = "manual" | "scheduled";

export interface Run {
  id: Uuid;
  config_id: Uuid;
  status: RunStatus;
  trigger: RunTrigger;
  started_at: IsoDateTime | null;
  completed_at: IsoDateTime | null;
  current_node: string | null;
  pdf_path: string | null;
  email_status: Record<string, unknown> | null;
  metrics: Record<string, unknown> | null;
  error: string | null;
  created_at: IsoDateTime;
}

export interface RunEvent {
  id: number;
  run_id: Uuid;
  ts: IsoDateTime;
  node: string | null;
  type: string;
  payload: Record<string, unknown>;
}

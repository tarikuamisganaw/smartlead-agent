export type ChatRequest = {
  conversation_id?: string;
  message: string;
};

export type TraceEvent = {
  id?: string;
  step_number?: number;
  agent_name?: string;
  node_name?: string;
  input_summary?: string | null;
  output_summary?: string | null;
  tool_name?: string | null;
  status?: string;
  error_message?: string | null;
  latency_ms?: number | null;
  created_at?: string;
};

export type ChatResponse = {
  conversation_id: string;
  agent_run_id: string;
  intent: string;
  requires_human_approval: boolean;
  lead_info: Record<string, unknown>;
  final_response: string;
  trace: TraceEvent[];
  anonymous_session_token?: string | null;
  total_latency_ms?: number | null;
  total_model_calls?: number | null;
  model_provider?: string | null;
  model_name?: string | null;
};

export type Lead = {
  id: string;
  conversation_id?: string;
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  business_type?: string | null;
  service_interest?: string | null;
  budget?: number | null;
  timeline?: string | null;
  lead_score?: number | null;
  lead_quality?: string | null;
  status?: string;
  created_at?: string;
  external_sync_status?: string | null;
  external_sync_provider?: string | null;
  external_sync_id?: string | null;
  external_synced_at?: string | null;
  external_sync_error?: string | null;
  last_sync_attempt_at?: string | null;
};

export type LeadSyncResponse = {
  lead: Lead;
  sync_result: {
    status: string;
    provider?: string;
    external_id?: string | null;
    message?: string;
  };
};

export type IntegrationStatus = {
  lead_sync: {
    provider: string;
    configured: boolean;
    automatic: boolean;
    sync_only_complete_leads: boolean;
    google_sheets: {
      credentials_configured: boolean;
      spreadsheet_configured: boolean;
      worksheet_name: string;
    };
  };
  notification: {
    provider: string;
    configured: boolean;
  };
};

export type AgentRun = {
  id: string;
  conversation_id: string;
  user_message: string;
  final_response?: string | null;
  status: string;
  started_at: string;
  finished_at?: string | null;
  total_latency_ms?: number | null;
  total_model_calls: number;
  estimated_cost: number;
  model_provider?: string | null;
  model_name?: string | null;
};

export type ConversationListItem = {
  id: string;
  created_at: string;
  updated_at: string;
  status: string;
  last_message?: string | null;
  latest_agent_run_id?: string | null;
};

export type ChatMessageRecord = {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};

export type ToolCall = {
  id: string;
  agent_run_id: string;
  tool_name: string;
  tool_input?: unknown;
  tool_output?: unknown;
  status: string;
  latency_ms?: number | null;
  created_at?: string;
};

export type AgentTraceResponse = {
  agent_run_id: string;
  trace: TraceEvent[];
  tool_calls?: ToolCall[];
};

export type ConversationResponse = {
  id: string;
  status: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessageRecord[];
  latest_lead?: Lead | null;
};

export type ConversationAgentRunsResponse = {
  conversation_id: string;
  agent_runs: AgentRun[];
};

export type DashboardSummary = {
  total_conversations: number;
  total_leads: number;
  hot_leads: number;
  warm_leads: number;
  cold_leads: number;
  pending_approvals: number;
  total_documents: number;
  total_document_chunks: number;
  recent_agent_runs: AgentRun[];
};

export type Approval = {
  id: string;
  agent_run_id: string;
  action_type: string;
  reason: string;
  draft_response?: string | null;
  status: string;
  created_at?: string;
  approved_at?: string | null;
};

export type RagResult = {
  chunk_id: string;
  document_id: string;
  title: string;
  source: string;
  content: string;
  score: number;
};

export type DocumentInfo = {
  id: string;
  title: string;
  source: string;
  created_at?: string;
  chunk_count: number;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
};

export type User = {
  id: string;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  created_at: string;
};

export type Membership = {
  organization_id: string;
  organization_name: string;
  role: string;
};

export type AuthTokenResponse = {
  access_token: string;
  token_type: "bearer";
  user: User;
};

export type AuthMeResponse = {
  user: User;
  memberships: Membership[];
};

export type AnonymousSessionResponse = {
  anonymous_session_id: string;
  session_token: string;
};

export type EvalCase = {
  id: string;
  input?: string;
  turns?: string[];
  [key: string]: unknown;
};

export type EvalMetrics = {
  intent_correct: number;
  rag_usage_correct: number;
  lead_extraction_correct: number;
  approval_correct: number;
  tool_call_correct: number;
  valid_output: number;
  average_latency_ms: number;
  estimated_cost: number;
};

export type EvalCaseResult = {
  case_id: string;
  passed: boolean;
  scores: Record<string, boolean>;
  expected: Record<string, unknown>;
  actual: Record<string, unknown>;
  errors: string[];
  latency_ms: number;
};

export type EvalRunResults = {
  provider: string;
  model?: string | null;
  total_cases: number;
  passed_cases: number;
  pass_rate: number;
  metrics: EvalMetrics;
  results: EvalCaseResult[];
};

export type LatestEvalResponse = EvalRunResults | {
  status: "missing";
  message: string;
  results: null;
};

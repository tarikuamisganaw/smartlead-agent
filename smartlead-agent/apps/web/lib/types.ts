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
  messages: Array<{
    id: string;
    conversation_id: string;
    role: "user" | "assistant";
    content: string;
    created_at: string;
  }>;
  latest_lead?: Lead | null;
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

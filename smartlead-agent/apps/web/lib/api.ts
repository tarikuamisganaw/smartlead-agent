import type {
  AgentRun,
  AgentTraceResponse,
  Approval,
  ChatRequest,
  ChatResponse,
  ConversationAgentRunsResponse,
  ConversationListItem,
  ConversationResponse,
  DashboardSummary,
  DocumentInfo,
  EvalCase,
  EvalRunResults,
  LatestEvalResponse,
  Lead,
  RagResult,
  AuthTokenResponse,
  AuthMeResponse,
  AnonymousSessionResponse,
} from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const AUTH_ENABLED = process.env.NEXT_PUBLIC_AUTH_ENABLED === "true";
const AUTH_TOKEN_KEY = "smartlead_access_token";
const ANON_TOKEN_KEY = "smartlead_anonymous_session_token";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const authToken = getAccessToken();
  const anonymousToken = getAnonymousSessionToken();
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      ...(anonymousToken ? { "X-Anonymous-Session-Token": anonymousToken } : {}),
      ...(options?.headers || {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = "";
    try {
      detail = JSON.stringify(await response.json());
    } catch {
      detail = await response.text();
    }
    throw new Error(`API request failed (${response.status}) ${detail}`.trim());
  }

  return response.json() as Promise<T>;
}

export function healthCheck() {
  return request<{ status: string; service: string }>("/health");
}

export function sendChatMessage(payload: ChatRequest) {
  return request<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function registerUser(payload: { email: string; password: string; full_name?: string; as_owner?: boolean }) {
  return request<AuthTokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginUser(payload: { email: string; password: string }) {
  return request<AuthTokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getMe() {
  return request<AuthMeResponse>("/auth/me");
}

export function createAnonymousSession() {
  return request<AnonymousSessionResponse>("/auth/anonymous-session", {
    method: "POST",
  });
}

export function claimAnonymousSession(sessionToken: string) {
  return request<{ claimed_conversations: number; claimed_leads: number }>("/auth/claim-anonymous-session", {
    method: "POST",
    body: JSON.stringify({ session_token: sessionToken }),
  });
}

export function getConversation(conversationId: string) {
  return request<ConversationResponse>(`/conversations/${conversationId}`);
}

export function getMyConversations() {
  return request<{ conversations: ConversationListItem[] }>("/my/conversations");
}

export function createMyConversation() {
  return request<{ conversation: ConversationListItem }>("/my/conversations/new", {
    method: "POST",
  });
}

export function getMyConversation(conversationId: string) {
  return request<ConversationResponse>(`/my/conversations/${conversationId}`);
}

export function getGuestConversations() {
  return request<{ conversations: ConversationListItem[] }>("/guest/conversations");
}

export function getConversations(limit = 25) {
  return request<{ conversations: ConversationListItem[] }>(`/conversations?limit=${limit}`);
}

export function getConversationAgentRuns(conversationId: string) {
  return request<ConversationAgentRunsResponse>(`/conversations/${conversationId}/agent-runs`);
}

export function getAgentRuns(limit = 25) {
  return request<{ agent_runs: AgentRun[] }>(`/agent-runs?limit=${limit}`);
}

export function getAgentTrace(agentRunId: string) {
  return request<AgentTraceResponse>(`/agent-runs/${agentRunId}/trace`);
}

export function getDashboardSummary() {
  return request<DashboardSummary>("/dashboard/summary");
}

export function getLeads() {
  return request<{ leads: Lead[] }>("/leads");
}

export function getApprovals() {
  return request<{ approvals: Approval[] }>("/approvals");
}

export function ingestDemoDocuments() {
  return request<{ documents_ingested: number; chunks_created: number }>("/documents/ingest-demo", {
    method: "POST",
  });
}

export function getDocuments() {
  return request<{ documents: DocumentInfo[] }>("/documents");
}

export function searchRag(query: string, topK = 4) {
  return request<{ query: string; results: RagResult[] }>("/rag/search", {
    method: "POST",
    body: JSON.stringify({ query, top_k: topK }),
  });
}

export function getEvalCases() {
  return request<{ cases: EvalCase[] }>("/evals/cases");
}

export function getLatestEvalResults() {
  return request<LatestEvalResponse>("/evals/latest");
}

export function runEvals() {
  return request<EvalRunResults>("/evals/run", {
    method: "POST",
  });
}

export function getAccessToken() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setAccessToken(token: string) {
  window.localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearAccessToken() {
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
}

export function getAnonymousSessionToken() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(ANON_TOKEN_KEY);
}

export function setAnonymousSessionToken(token: string) {
  window.localStorage.setItem(ANON_TOKEN_KEY, token);
}

export function clearAnonymousSessionToken() {
  window.localStorage.removeItem(ANON_TOKEN_KEY);
}

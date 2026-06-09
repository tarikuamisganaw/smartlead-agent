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
  Lead,
  RagResult,
} from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
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

export function getConversation(conversationId: string) {
  return request<ConversationResponse>(`/conversations/${conversationId}`);
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

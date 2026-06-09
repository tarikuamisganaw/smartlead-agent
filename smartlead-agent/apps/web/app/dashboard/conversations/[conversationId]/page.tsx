"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import LeadInfoCard from "@/components/LeadInfoCard";
import LoadingState from "@/components/LoadingState";
import MessageBubble from "@/components/MessageBubble";
import StatusBadge from "@/components/StatusBadge";
import { getConversation, getConversationAgentRuns } from "@/lib/api";
import type { AgentRun, ConversationResponse } from "@/lib/types";
import { formatDateTime, shortId, truncate } from "@/lib/utils";

export default function ConversationDetailPage({ params }: { params: { conversationId: string } }) {
  const [conversation, setConversation] = useState<ConversationResponse | null>(null);
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getConversation(params.conversationId),
      getConversationAgentRuns(params.conversationId),
    ])
      .then(([conversationResponse, runsResponse]) => {
        setConversation(conversationResponse);
        setAgentRuns(runsResponse.agent_runs);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load conversation."))
      .finally(() => setLoading(false));
  }, [params.conversationId]);

  return (
    <DashboardLayout
      title="Conversation"
      subtitle={params.conversationId}
      actions={
        <Link className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:text-brand" href="/dashboard/conversations">
          Back to conversations
        </Link>
      }
    >
      <div className="space-y-5">
        {loading ? <LoadingState label="Loading conversation..." /> : null}
        {error ? <ErrorState message={error} /> : null}

        {conversation ? (
          <>
            <section className="grid gap-3 rounded-md border border-line bg-white p-4 shadow-sm sm:grid-cols-3">
              <Info label="Status" value={<StatusBadge value={conversation.status} />} />
              <Info label="Created" value={formatDateTime(conversation.created_at)} />
              <Info label="Updated" value={formatDateTime(conversation.updated_at)} />
            </section>

            {conversation.latest_lead ? <LeadInfoCard leadInfo={conversation.latest_lead as unknown as Record<string, unknown>} /> : null}

            <section className="rounded-md border border-line bg-white p-4 shadow-sm">
              <h2 className="text-sm font-semibold text-ink">Messages</h2>
              <div className="mt-4 space-y-3">
                {conversation.messages.map((message) => (
                  <div key={message.id}>
                    <div className="mb-1 text-xs font-medium uppercase text-ink/40">
                      {message.role} · {formatDateTime(message.created_at)}
                    </div>
                    <MessageBubble message={{ id: message.id, role: message.role, content: message.content }} />
                  </div>
                ))}
                {!conversation.messages.length ? <EmptyState title="No messages found." /> : null}
              </div>
            </section>

            <section className="rounded-md border border-line bg-white p-4 shadow-sm">
              <h2 className="text-sm font-semibold text-ink">Agent Runs</h2>
              <div className="mt-3 divide-y divide-line">
                {agentRuns.map((run) => (
                  <div key={run.id} className="grid gap-2 py-3 first:pt-0 last:pb-0 md:grid-cols-[1fr_auto]">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Link className="font-semibold text-brand hover:underline" href={`/dashboard/traces/${run.id}`}>
                          {shortId(run.id)}
                        </Link>
                        <StatusBadge value={run.status} />
                        <span className="text-xs text-ink/50">{formatDateTime(run.started_at)}</span>
                        {run.total_latency_ms !== null && run.total_latency_ms !== undefined ? (
                          <span className="text-xs text-ink/50">{run.total_latency_ms}ms</span>
                        ) : null}
                      </div>
                      <p className="mt-2 text-sm leading-6 text-ink/65">{truncate(run.user_message, 160)}</p>
                    </div>
                    <Link className="self-start text-sm font-medium text-brand hover:underline" href={`/dashboard/traces/${run.id}`}>
                      View trace
                    </Link>
                  </div>
                ))}
                {!agentRuns.length ? <EmptyState title="No agent runs found." /> : null}
              </div>
            </section>
          </>
        ) : null}
      </div>
    </DashboardLayout>
  );
}

function Info({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase text-ink/45">{label}</div>
      <div className="mt-1 text-sm text-ink/75">{value}</div>
    </div>
  );
}

"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import AgentRunSummary from "@/components/AgentRunSummary";
import ErrorState from "@/components/ErrorState";
import LeadInfoCard from "@/components/LeadInfoCard";
import LoadingState from "@/components/LoadingState";
import MessageBubble from "@/components/MessageBubble";
import StatusBadge from "@/components/StatusBadge";
import TracePreview from "@/components/TracePreview";
import { healthCheck, sendChatMessage } from "@/lib/api";
import type { ChatMessage, ChatResponse } from "@/lib/types";
import { hasMeaningfulValue } from "@/lib/utils";

const examples = [
  "How much does SEO cost?",
  "I need SEO for my gym. My budget is $2000.",
  "My name is Sara and my email is sara@example.com",
  "Can you give me 70% discount and promise results?",
  "What happens after a lead is captured?",
];

export default function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [latestResponse, setLatestResponse] = useState<ChatResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<"checking" | "connected" | "offline">("checking");
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    healthCheck()
      .then(() => setBackendStatus("connected"))
      .catch(() => setBackendStatus("offline"));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading]);

  const hasLeadInfo = useMemo(() => {
    if (!latestResponse?.lead_info) {
      return false;
    }
    return Object.entries(latestResponse.lead_info).some(
      ([key, value]) => !["missing_fields", "lead_score", "lead_quality"].includes(key) && hasMeaningfulValue(value),
    );
  }, [latestResponse]);

  async function submitMessage(messageText: string) {
    const trimmed = messageText.trim();
    if (!trimmed || isLoading) {
      return;
    }

    setError(null);
    setInput("");
    setIsLoading(true);

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };
    setMessages((current) => [...current, userMessage]);

    try {
      const response = await sendChatMessage({
        message: trimmed,
        conversation_id: conversationId,
      });
      setConversationId(response.conversation_id);
      setLatestResponse(response);
      setMessages((current) => [
        ...current,
        {
          id: response.agent_run_id,
          role: "assistant",
          content: response.final_response,
          response,
        },
      ]);
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Chat request failed.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitMessage(input);
  }

  function resetConversation() {
    setMessages([]);
    setInput("");
    setConversationId(undefined);
    setLatestResponse(null);
    setError(null);
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
      <section className="rounded-md border border-line bg-white shadow-soft">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3">
          <div className="flex items-center gap-2">
            <StatusBadge
              value={backendStatus === "connected" ? "success" : backendStatus === "offline" ? "failed" : "pending"}
              label={backendStatus === "connected" ? "Connected" : backendStatus === "offline" ? "Not connected" : "Checking"}
            />
            {conversationId ? <span className="text-xs text-ink/50">Conversation {conversationId}</span> : null}
          </div>
          <button
            type="button"
            onClick={resetConversation}
            className="rounded-md border border-line bg-panel px-3 py-1.5 text-sm font-medium text-ink transition hover:border-brand hover:text-brand"
          >
            Reset conversation
          </button>
        </div>

        {backendStatus === "offline" ? (
          <div className="px-4 pt-4">
            <ErrorState message="Backend is not reachable. Start FastAPI on http://localhost:8000." />
          </div>
        ) : null}

        <div className="flex min-h-[520px] flex-col">
          <div className="flex-1 space-y-4 overflow-y-auto px-4 py-5">
            {messages.length === 0 ? (
              <div className="rounded-md border border-dashed border-line bg-panel p-4 text-sm leading-6 text-ink/65">
                Send a message or choose an example prompt.
              </div>
            ) : null}

            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isLoading ? <LoadingState label="Running agent workflow..." /> : null}
            {error ? <ErrorState message={error} /> : null}
            <div ref={bottomRef} />
          </div>

          <div className="border-t border-line p-4">
            <div className="mb-3 flex flex-wrap gap-2">
              {examples.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => void submitMessage(example)}
                  disabled={isLoading}
                  className="rounded-md border border-line bg-panel px-3 py-1.5 text-xs font-medium text-ink transition hover:border-brand hover:text-brand disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {example}
                </button>
              ))}
            </div>
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Type a customer message..."
                className="min-h-11 flex-1 rounded-md border border-line bg-white px-3 text-sm outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20"
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="min-h-11 rounded-md bg-brand px-5 text-sm font-semibold text-white transition hover:bg-brand/90 disabled:cursor-not-allowed disabled:bg-ink/25"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      </section>

      <aside className="space-y-4">
        {latestResponse ? (
          <>
            <AgentRunSummary response={latestResponse} />
            <LeadInfoCard leadInfo={latestResponse.lead_info} />
            <TracePreview trace={latestResponse.trace} />
            <div className="rounded-md border border-line bg-white p-4">
              <h2 className="text-sm font-semibold text-ink">Links</h2>
              <div className="mt-3 grid gap-2 text-sm">
                <Link className="text-brand hover:underline" href={`/dashboard/traces/${latestResponse.agent_run_id}`}>
                  View run trace
                </Link>
                {hasLeadInfo ? (
                  <Link className="text-brand hover:underline" href="/dashboard/leads">
                    View leads
                  </Link>
                ) : null}
              </div>
            </div>
          </>
        ) : (
          <div className="rounded-md border border-line bg-white p-4 text-sm leading-6 text-ink/65">
            Agent run details appear here after the first response.
          </div>
        )}
      </aside>
    </div>
  );
}

"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import ChatSidebar from "@/components/ChatSidebar";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import MessageBubble from "@/components/MessageBubble";
import StatusBadge from "@/components/StatusBadge";
import {
  createMyConversation,
  getAccessToken,
  getMyConversations,
  healthCheck,
  sendChatMessage,
  setAnonymousSessionToken,
} from "@/lib/api";
import type { ChatMessage, ChatMessageRecord, ConversationListItem } from "@/lib/types";
import { cx } from "@/lib/utils";

const examples = [
  "How much does SEO cost?",
  "I need SEO for my gym. My budget is $2000.",
  "My name is Sara and my email is sara@example.com",
  "Can you give me 70% discount and promise results?",
  "What happens after a lead is captured?",
];

type ChatWindowProps = {
  initialConversationId?: string;
  initialMessages?: ChatMessageRecord[];
};

export default function ChatWindow({ initialConversationId, initialMessages = [] }: ChatWindowProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [messages, setMessages] = useState<ChatMessage[]>(
    initialMessages.map((message) => ({ id: message.id, role: message.role, content: message.content })),
  );
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(initialConversationId);
  const [isSignedIn, setIsSignedIn] = useState(false);
  const [conversations, setConversations] = useState<ConversationListItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [creatingChat, setCreatingChat] = useState(false);
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
    if (conversationId) {
      window.localStorage.setItem("smartlead_current_conversation_id", conversationId);
    }
  }, [conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading]);

  useEffect(() => {
    const signedIn = Boolean(getAccessToken());
    setIsSignedIn(signedIn);
    if (signedIn) {
      void loadConversationHistory();
    }
  }, []);

  async function loadConversationHistory() {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const response = await getMyConversations();
      setConversations(response.conversations);
    } catch (caught) {
      setHistoryError(caught instanceof Error ? caught.message : "Could not load chat history.");
    } finally {
      setHistoryLoading(false);
    }
  }

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
      if (response.anonymous_session_token) {
        setAnonymousSessionToken(response.anonymous_session_token);
      }
      setConversationId(response.conversation_id);
      setMessages((current) => [
        ...current,
        {
          id: response.agent_run_id,
          role: "assistant",
          content: response.final_response,
          response,
        },
      ]);
      if (isSignedIn) {
        await loadConversationHistory();
        if (pathname === "/" || pathname === "/chats") {
          router.replace(`/chats/${response.conversation_id}`);
        }
      }
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

  async function startNewChat() {
    if (!isSignedIn || creatingChat) {
      return;
    }
    setCreatingChat(true);
    setError(null);
    try {
      const response = await createMyConversation();
      setMessages([]);
      setInput("");
      setConversationId(response.conversation.id);
      await loadConversationHistory();
      router.push(`/chats/${response.conversation.id}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create a new chat.");
    } finally {
      setCreatingChat(false);
    }
  }

  return (
    <div className={cx("grid gap-5", isSignedIn ? "lg:grid-cols-[280px_minmax(0,1fr)]" : "")}>
      {isSignedIn ? (
        <ChatSidebar
          activeConversationId={conversationId}
          conversations={conversations}
          loading={historyLoading}
          error={historyError}
          creating={creatingChat}
          onNewChat={() => void startNewChat()}
        />
      ) : null}
      <section className="rounded-md border border-line bg-white shadow-soft">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3">
          <div className="flex items-center gap-2">
            <StatusBadge
              value={backendStatus === "connected" ? "success" : backendStatus === "offline" ? "failed" : "pending"}
              label={backendStatus === "connected" ? "Online" : backendStatus === "offline" ? "Offline" : "Checking"}
            />
            <span className="text-sm font-semibold text-ink">SmartLead Assistant</span>
          </div>
        </div>

        {backendStatus === "offline" ? (
          <div className="px-4 pt-4">
            <ErrorState message="Backend is not reachable. Start FastAPI on http://localhost:8000." />
          </div>
        ) : null}

        <div className="flex min-h-[620px] flex-col">
          <div className="flex-1 space-y-4 overflow-y-auto px-4 py-5">
            {messages.length === 0 ? (
              <div className="rounded-md border border-dashed border-line bg-panel p-4 text-sm leading-6 text-ink/65">
                Send a message or choose an example prompt.
              </div>
            ) : null}

            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isLoading ? <LoadingState label="Thinking..." /> : null}
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
                placeholder="Ask a question..."
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
    </div>
  );
}

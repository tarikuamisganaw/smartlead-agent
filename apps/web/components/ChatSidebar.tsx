"use client";

import Link from "next/link";
import LoadingState from "@/components/LoadingState";
import type { ConversationListItem } from "@/lib/types";
import { cx, formatDateTime, shortId, truncate } from "@/lib/utils";

type ChatSidebarProps = {
  activeConversationId?: string;
  conversations: ConversationListItem[];
  loading?: boolean;
  error?: string | null;
  creating?: boolean;
  onNewChat: () => void;
};

export default function ChatSidebar({
  activeConversationId,
  conversations,
  loading = false,
  error = null,
  creating = false,
  onNewChat,
}: ChatSidebarProps) {
  return (
    <aside className="min-h-[620px] rounded-md border border-line bg-white shadow-soft lg:sticky lg:top-5 lg:self-start">
      <div className="flex items-center justify-between border-b border-line px-3 py-3">
        <div>
          <p className="text-xs font-semibold uppercase text-ink/45">Chats</p>
          <p className="text-sm font-semibold text-ink">History</p>
        </div>
        <button
          type="button"
          onClick={onNewChat}
          disabled={creating}
          aria-label="New chat"
          title="New chat"
          className="grid h-9 w-9 place-items-center rounded-md border border-line bg-panel text-xl font-semibold leading-none text-ink transition hover:border-brand hover:text-brand disabled:cursor-not-allowed disabled:opacity-60"
        >
          +
        </button>
      </div>
      <div className="max-h-[calc(100vh-120px)] overflow-y-auto p-2">
        {loading ? <div className="p-2"><LoadingState label="Loading chats..." /></div> : null}
        {error ? <p className="p-2 text-sm text-accent">{error}</p> : null}
        {!loading && !error && conversations.length === 0 ? (
          <p className="p-2 text-sm leading-6 text-ink/60">No saved chats yet.</p>
        ) : null}
        <nav className="grid gap-1">
          {conversations.map((conversation) => {
            const active = conversation.id === activeConversationId;
            return (
              <Link
                key={conversation.id}
                href={`/chats/${conversation.id}`}
                className={cx(
                  "rounded-md px-3 py-2 text-sm transition",
                  active ? "bg-brand text-white" : "text-ink/75 hover:bg-panel hover:text-brand",
                )}
              >
                <span className="block font-semibold">{truncate(conversation.last_message, 54)}</span>
                <span className={cx("mt-1 block text-xs", active ? "text-white/75" : "text-ink/45")}>
                  {formatDateTime(conversation.updated_at)} · {shortId(conversation.id, 4)}
                </span>
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}

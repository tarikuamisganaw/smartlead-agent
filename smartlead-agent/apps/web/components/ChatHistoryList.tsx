import Link from "next/link";
import type { ConversationListItem } from "@/lib/types";
import { formatDateTime, shortId, truncate } from "@/lib/utils";

export default function ChatHistoryList({ conversations }: { conversations: ConversationListItem[] }) {
  return (
    <div className="grid gap-3">
      {conversations.map((conversation) => (
        <Link
          key={conversation.id}
          href={`/chats/${conversation.id}`}
          className="rounded-md border border-line bg-white p-4 shadow-sm transition hover:border-brand"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="font-semibold text-brand">{shortId(conversation.id)}</span>
            <span className="text-xs text-ink/50">{formatDateTime(conversation.updated_at)}</span>
          </div>
          <p className="mt-2 text-sm leading-6 text-ink/65">{truncate(conversation.last_message, 160)}</p>
        </Link>
      ))}
    </div>
  );
}

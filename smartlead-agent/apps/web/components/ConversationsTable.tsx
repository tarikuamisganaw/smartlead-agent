import type { ReactNode } from "react";
import Link from "next/link";
import StatusBadge from "@/components/StatusBadge";
import type { ConversationListItem } from "@/lib/types";
import { formatDateTime, shortId, truncate } from "@/lib/utils";

export default function ConversationsTable({ conversations }: { conversations: ConversationListItem[] }) {
  return (
    <div className="overflow-x-auto rounded-md border border-line bg-white shadow-sm">
      <table className="min-w-[860px] w-full border-collapse text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-ink/50">
          <tr>
            <Th>Conversation</Th>
            <Th>Status</Th>
            <Th>Last message</Th>
            <Th>Created</Th>
            <Th>Updated</Th>
            <Th>Trace</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {conversations.map((conversation) => (
            <tr key={conversation.id}>
              <Td>
                <Link className="font-semibold text-brand hover:underline" href={`/dashboard/conversations/${conversation.id}`}>
                  {shortId(conversation.id)}
                </Link>
              </Td>
              <Td><StatusBadge value={conversation.status} /></Td>
              <Td>{truncate(conversation.last_message, 100)}</Td>
              <Td>{formatDateTime(conversation.created_at)}</Td>
              <Td>{formatDateTime(conversation.updated_at)}</Td>
              <Td>
                {conversation.latest_agent_run_id ? (
                  <Link className="text-brand hover:underline" href={`/dashboard/traces/${conversation.latest_agent_run_id}`}>
                    Latest trace
                  </Link>
                ) : (
                  "—"
                )}
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children: ReactNode }) {
  return <th className="px-4 py-3 font-semibold">{children}</th>;
}

function Td({ children }: { children: ReactNode }) {
  return <td className="px-4 py-3 text-ink/75">{children}</td>;
}

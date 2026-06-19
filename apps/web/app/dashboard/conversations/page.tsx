"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ConversationsTable from "@/components/ConversationsTable";
import DashboardLayout from "@/components/DashboardLayout";
import EmptyState from "@/components/EmptyState";
import ErrorState from "@/components/ErrorState";
import LoadingState from "@/components/LoadingState";
import { getConversations } from "@/lib/api";
import type { ConversationListItem } from "@/lib/types";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<ConversationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getConversations()
      .then((response) => setConversations(response.conversations))
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load conversations."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout
      title="Conversations"
      subtitle="Recent customer conversations and their latest trace links."
      actions={
        <Link className="rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:text-brand" href="/">
          Start conversation
        </Link>
      }
    >
      <div className="space-y-4">
        {loading ? <LoadingState label="Loading conversations..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {!loading && !error && conversations.length ? <ConversationsTable conversations={conversations} /> : null}
        {!loading && !error && !conversations.length ? (
          <EmptyState title="No conversations yet." message="Start from the chat demo." />
        ) : null}
      </div>
    </DashboardLayout>
  );
}

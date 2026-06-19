"use client";

import { useRouter } from "next/navigation";
import { createMyConversation, getAccessToken } from "@/lib/api";

export default function NewChatButton() {
  const router = useRouter();

  async function startNewChat() {
    if (getAccessToken()) {
      const response = await createMyConversation();
      router.push(`/chats/${response.conversation.id}`);
      return;
    }
    router.push("/");
  }

  return (
    <button type="button" onClick={startNewChat} className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand/90">
      New chat
    </button>
  );
}

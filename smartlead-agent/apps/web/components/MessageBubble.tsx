import type { ChatMessage } from "@/lib/types";
import { cx } from "@/lib/utils";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={cx("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cx(
          "max-w-[88%] rounded-md border px-4 py-3 text-sm leading-6 shadow-sm",
          isUser
            ? "border-brand bg-brand text-white"
            : "border-line bg-white text-ink",
        )}
      >
        {message.content}
      </div>
    </div>
  );
}

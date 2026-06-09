import type { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  message?: string;
  action?: ReactNode;
};

export default function EmptyState({ title, message, action }: EmptyStateProps) {
  return (
    <div className="rounded-md border border-dashed border-line bg-panel px-4 py-5">
      <p className="text-sm font-semibold text-ink">{title}</p>
      {message ? <p className="mt-2 text-sm leading-6 text-ink/65">{message}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

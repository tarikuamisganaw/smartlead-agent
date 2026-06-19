export default function LoadingState({ label = "Working..." }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-ink/60">
      <span className="h-2 w-2 animate-pulse rounded-full bg-brand" />
      <span>{label}</span>
    </div>
  );
}

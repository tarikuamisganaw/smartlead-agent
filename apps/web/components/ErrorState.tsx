export default function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-accent/30 bg-accent/10 px-3 py-2 text-sm text-accent">
      {message}
    </div>
  );
}

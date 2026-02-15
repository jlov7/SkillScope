export default function EmptyState({
  title,
  body,
  cta,
}: {
  title: string;
  body: string;
  cta?: React.ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-dashed border-[var(--border)] p-8 bg-white">
      <h2 className="text-2xl font-semibold mb-2">{title}</h2>
      <p className="text-[var(--muted)] mb-4">{body}</p>
      {cta}
    </div>
  );
}

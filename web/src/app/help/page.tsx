import Shell from "@/components/Shell";

export default function HelpPage() {
  return (
    <Shell>
      <div className="space-y-4">
        <h1 className="text-3xl font-semibold">Help</h1>
        <p className="text-[var(--muted)]">
          This UI analyzes SkillScope JSON/JSONL locally in your browser. For CLI workflows, see the
          README.
        </p>
        <ul className="list-disc pl-5 text-[var(--muted)]">
          <li>Use Start for the fastest first-run path (`/start`).</li>
          <li>Use Why for audience-specific explanation (`/why`).</li>
          <li>Use `skillscope emit --demo` to generate sample events.</li>
          <li>Upload JSON/JSONL files on Analyze for single-run summaries.</li>
          <li>Use Studio to compare baseline vs current runs and replay timeline steps.</li>
          <li>Use `/studio?demo=1&guide=1` for a guided presenter demo.</li>
          <li>Use Demo Kit for scripted presentations and fallback plan (`/demo-kit`).</li>
        </ul>
      </div>
    </Shell>
  );
}

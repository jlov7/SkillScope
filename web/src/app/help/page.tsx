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
          <li>Use `skillscope emit --demo` to generate sample events.</li>
          <li>Upload JSON/JSONL files on the Analyze page.</li>
          <li>Use the Demo page for a guided preview.</li>
        </ul>
      </div>
    </Shell>
  );
}

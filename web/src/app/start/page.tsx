import Link from "next/link";

import Shell from "@/components/Shell";

export default function StartPage() {
  return (
    <Shell>
      <div className="space-y-8">
        <section className="space-y-4">
          <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">Start</p>
          <h1 className="text-3xl font-semibold">Try SkillScope in 60 seconds</h1>
          <p className="text-[var(--muted)] max-w-3xl">
            This flow is optimized for first-time users and live demos. No setup, no account, and no
            backend required.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/studio?demo=1&guide=1"
              className="px-4 py-2 rounded-full bg-[var(--accent)] text-white"
            >
              Run guided Studio demo
            </Link>
            <Link href="/why" className="px-4 py-2 rounded-full border border-[var(--border)]">
              Understand why it matters
            </Link>
            <Link href="/demo-kit" className="px-4 py-2 rounded-full border border-[var(--border)]">
              Open presenter kit
            </Link>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <article className="rounded-2xl border border-[var(--border)] bg-white p-5">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">Step 1</p>
            <h2 className="text-xl font-semibold mt-1">Load demo runs</h2>
            <p className="text-sm text-[var(--muted)] mt-2">
              Simulate a baseline-vs-regression scenario instantly with realistic event data.
            </p>
          </article>
          <article className="rounded-2xl border border-[var(--border)] bg-white p-5">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">Step 2</p>
            <h2 className="text-xl font-semibold mt-1">Replay behavior</h2>
            <p className="text-sm text-[var(--muted)] mt-2">
              Walk through timeline steps to show where behavior diverged and why.
            </p>
          </article>
          <article className="rounded-2xl border border-[var(--border)] bg-white p-5">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">Step 3</p>
            <h2 className="text-xl font-semibold mt-1">Land on action</h2>
            <p className="text-sm text-[var(--muted)] mt-2">
              Use root-cause insights and skill-level deltas to define a concrete next fix.
            </p>
          </article>
        </section>

        <section className="rounded-3xl border border-[var(--border)] bg-white p-6">
          <h2 className="text-2xl font-semibold">Next after first run</h2>
          <ul className="mt-3 list-disc pl-5 text-[var(--muted)] space-y-1">
            <li>Bring your own JSON/JSONL data to Studio for real regressions.</li>
            <li>Use Analyze for single-run summaries.</li>
            <li>Use Why + Demo Kit for stakeholder communication.</li>
          </ul>
        </section>
      </div>
    </Shell>
  );
}

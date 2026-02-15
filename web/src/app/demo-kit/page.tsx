import Link from "next/link";

import Shell from "@/components/Shell";

export default function DemoKitPage() {
  return (
    <Shell>
      <div className="space-y-8">
        <section className="space-y-4">
          <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">Demo Kit</p>
          <h1 className="text-3xl font-semibold">Presenter-ready scripts and flow</h1>
          <p className="text-[var(--muted)] max-w-3xl">
            Use these scripts to demo SkillScope confidently at different time budgets while keeping
            the message crisp and actionable.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/studio?demo=1&guide=1"
              className="px-4 py-2 rounded-full bg-[var(--accent)] text-white"
            >
              Launch guided demo
            </Link>
            <a
              href="https://skillscope-amber.vercel.app/studio?demo=1&guide=1"
              className="px-4 py-2 rounded-full border border-[var(--border)]"
            >
              Public demo URL
            </a>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <article className="rounded-2xl border border-[var(--border)] bg-white p-5">
            <h2 className="text-xl font-semibold">90-second script</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Problem, quick guided replay, one key regression insight, one concrete engineering action.
            </p>
          </article>
          <article className="rounded-2xl border border-[var(--border)] bg-white p-5">
            <h2 className="text-xl font-semibold">5-minute script</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Full workflow, top metric deltas, root-cause cards, and skill-level remediation plan.
            </p>
          </article>
          <article className="rounded-2xl border border-[var(--border)] bg-white p-5">
            <h2 className="text-xl font-semibold">15-minute deep dive</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Technical architecture, semantic conventions, observability integration, and roadmap.
            </p>
          </article>
        </section>

        <section className="rounded-3xl border border-[var(--border)] bg-white p-6 space-y-3">
          <h2 className="text-2xl font-semibold">Fail-safe backup plan</h2>
          <ul className="list-disc pl-5 text-[var(--muted)] space-y-1">
            <li>Use the same guided URL to avoid setup drift.</li>
            <li>If network is unstable, rely on the built-in demo data and screenshots in docs.</li>
            <li>If time is cut short, show only summary + root causes + skill deltas.</li>
            <li>Always end on a concrete “next fix” recommendation.</li>
          </ul>
        </section>

        <section className="rounded-3xl border border-[var(--border)] bg-white p-6">
          <p className="text-sm text-[var(--muted)]">
            Detailed scripts and speaking notes are in{" "}
            <a
              href="https://github.com/jlov7/SkillScope/blob/master/docs/demo-kit.md"
              className="underline hover:no-underline"
            >
              docs/demo-kit.md
            </a>{" "}
            in the repository.
          </p>
        </section>
      </div>
    </Shell>
  );
}

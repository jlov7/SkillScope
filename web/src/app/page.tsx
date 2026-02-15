"use client";

import Link from "next/link";
import { useState } from "react";

import Shell from "@/components/Shell";

export default function HomePage() {
  const [seen, setSeen] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.localStorage.getItem("skillscope_seen_onboarding") === "1";
  });

  const markSeen = () => {
    window.localStorage.setItem("skillscope_seen_onboarding", "1");
    setSeen(true);
  };

  return (
    <Shell>
      <section className="grid gap-8 lg:grid-cols-2">
        <div className="space-y-5">
          <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">
            Research-only preview
          </p>
          <h1 className="text-4xl font-semibold">SkillScope Research UI</h1>
          <p className="text-lg text-[var(--muted)]">
            SkillScope adds observability to Agent Skills. This UI runs entirely in your browser—no
            uploads, no servers.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/analyze" className="px-4 py-2 rounded-full bg-[var(--accent)] text-white">
              Analyze data
            </Link>
            <Link href="/studio" className="px-4 py-2 rounded-full border border-[var(--border)]">
              Open Studio
            </Link>
            <Link
              href="/demo"
              className="px-4 py-2 rounded-full border border-[var(--border)]"
            >
              Load demo
            </Link>
          </div>
        </div>
        <div className="rounded-3xl bg-white border border-[var(--border)] p-6 shadow-sm">
          <h2 className="text-2xl font-semibold mb-3">First run checklist</h2>
          <ol className="space-y-2 text-[var(--muted)]">
            <li>1. Export events via `skillscope emit` or `skillscope ingest`.</li>
            <li>2. Upload JSON/JSONL on the Analyze page.</li>
            <li>3. Use Studio to replay baseline vs current runs.</li>
            <li>4. Share insights and root-cause notes with your team.</li>
          </ol>
          {!seen && (
            <button
              onClick={markSeen}
              className="mt-5 px-4 py-2 rounded-full bg-[var(--accent-2)] text-white"
            >
              Mark onboarding complete
            </button>
          )}
        </div>
      </section>
    </Shell>
  );
}

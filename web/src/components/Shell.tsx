import Link from "next/link";

export default function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="px-6 py-5 border-b border-[var(--border)] bg-[var(--panel)]">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-[var(--accent)] text-white flex items-center justify-center font-semibold">
              S
            </div>
            <div>
              <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">SkillScope</p>
              <p className="text-lg font-semibold">Research UI</p>
            </div>
          </div>
          <nav className="flex flex-wrap gap-4 text-sm">
            <Link href="/" className="hover:underline">
              Home
            </Link>
            <Link href="/analyze" className="hover:underline">
              Analyze
            </Link>
            <Link href="/demo" className="hover:underline">
              Demo
            </Link>
            <Link href="/help" className="hover:underline">
              Help
            </Link>
          </nav>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-6 py-10">{children}</main>
      <footer className="px-6 py-6 border-t border-[var(--border)] text-sm text-[var(--muted)]">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-2">
          <span>SkillScope is research-only software. Use at your own risk.</span>
          <span>Client-side analysis. No data leaves your browser.</span>
        </div>
      </footer>
    </div>
  );
}

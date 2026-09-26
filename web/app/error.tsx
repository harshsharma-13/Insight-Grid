"use client";

import Link from "next/link";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <section className="system-state" role="alert">
    <span className="section-kicker">Workspace interrupted</span>
    <h1>The evidence view could not be prepared.</h1>
    <p>Your data has not been changed. Retry the workspace or return to the market overview.</p>
    <div><button type="button" onClick={reset}>Try again</button><Link href="/">Return to overview</Link></div>
  </section>;
}

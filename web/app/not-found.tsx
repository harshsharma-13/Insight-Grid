import Link from "next/link";

export default function NotFound() {
  return <section className="system-state">
    <span className="section-kicker">Workspace not found</span>
    <h1>That intelligence view does not exist.</h1>
    <p>Use the ribbon to continue exploring the current smartphone evidence snapshot.</p>
    <div><Link href="/">Return to overview</Link><Link href="/intelligence">Open Intelligence</Link></div>
  </section>;
}

import { env } from "cloudflare:workers";

type Statement = { bind: (...values: unknown[]) => Statement; run: () => Promise<unknown> };
type Database = { prepare: (sql: string) => Statement; batch: (statements: Statement[]) => Promise<unknown> };
type RuntimeEnv = { DB?: Database };
const runtime = env as unknown as RuntimeEnv;

const telemetrySchema = `
CREATE TABLE IF NOT EXISTS telemetry_events (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  route TEXT NOT NULL,
  value REAL,
  detail_json TEXT NOT NULL,
  created_at TEXT NOT NULL
)`;
const telemetryIndex = `CREATE INDEX IF NOT EXISTS idx_telemetry_events_owner_created ON telemetry_events(owner_id, created_at DESC)`;

export async function POST(request: Request) {
  const owner = request.headers.get("oai-authenticated-user-id") || (new URL(request.url).hostname === "localhost" ? "local-preview" : null);
  if (!owner || !runtime.DB) return new Response(null, { status: owner ? 503 : 401 });
  try {
    const payload = await request.json() as { eventType?: string; route?: string; value?: number; detail?: Record<string, unknown> };
    const eventType = String(payload.eventType || "unknown").slice(0, 60);
    const route = String(payload.route || "/").slice(0, 180);
    const detail = JSON.stringify(payload.detail || {}).slice(0, 1600);
    await runtime.DB.batch([runtime.DB.prepare(telemetrySchema), runtime.DB.prepare(telemetryIndex)]);
    await runtime.DB.prepare("INSERT INTO telemetry_events (id, owner_id, event_type, route, value, detail_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)").bind(crypto.randomUUID(), owner, eventType, route, Number.isFinite(payload.value) ? payload.value : null, detail, new Date().toISOString()).run();
    return new Response(null, { status: 204 });
  } catch {
    return new Response(null, { status: 400 });
  }
}

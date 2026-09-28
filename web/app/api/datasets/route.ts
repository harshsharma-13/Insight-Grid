import { env } from "cloudflare:workers";
import { datasetVersionsOwnerIndex, datasetVersionsSchema } from "@/db/schema";

type Statement = { bind: (...values: unknown[]) => Statement; run: () => Promise<unknown>; all: <T>() => Promise<{ results: T[] }>; first: <T>() => Promise<T | null> };
type Database = { prepare: (sql: string) => Statement; batch: (statements: Statement[]) => Promise<unknown> };
type StoredObject = { body: ReadableStream; httpMetadata?: { contentType?: string } };
type Bucket = { put: (key: string, value: ArrayBuffer, options?: { httpMetadata?: { contentType?: string } }) => Promise<unknown>; get: (key: string) => Promise<StoredObject | null> };
type RuntimeEnv = { DB?: Database; UPLOADS?: Bucket };
type Row = Record<string, unknown>;

const MAX_BYTES = 8 * 1024 * 1024;
const runtime = env as unknown as RuntimeEnv;

function ownerId(request: Request) {
  const hostname = new URL(request.url).hostname;
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "[::1]" ? "local-preview" : null;
}

async function database() {
  if (!runtime.DB) throw new Error("Dataset database is unavailable");
  await runtime.DB.batch([runtime.DB.prepare(datasetVersionsSchema), runtime.DB.prepare(datasetVersionsOwnerIndex)]);
  return runtime.DB;
}

function parseCsv(text: string) {
  const rows: string[][] = [];
  let row: string[] = [];
  let value = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (char === '"' && quoted && text[index + 1] === '"') { value += '"'; index += 1; }
    else if (char === '"') quoted = !quoted;
    else if (char === "," && !quoted) { row.push(value); value = ""; }
    else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && text[index + 1] === "\n") index += 1;
      row.push(value); if (row.some((cell) => cell.trim())) rows.push(row); row = []; value = "";
    } else value += char;
  }
  row.push(value); if (row.some((cell) => cell.trim())) rows.push(row);
  const headers = (rows.shift() || []).map((header) => header.trim());
  return rows.map((cells) => Object.fromEntries(headers.map((header, index) => [header, cells[index]?.trim() || ""])));
}

function analyze(rows: Row[]) {
  const columns = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
  const findColumn = (patterns: RegExp[]) => columns.find((column) => patterns.some((pattern) => pattern.test(column.toLowerCase())));
  const reviewColumn = findColumn([/^review_text$/, /^review$/, /comment/, /content/, /^text$/]);
  const phoneColumn = findColumn([/^phone_id$/, /^phone_name$/, /product/]);
  const brandColumn = findColumn([/^brand$/, /manufacturer/]);
  const platformColumn = findColumn([/^platform$/, /source/, /marketplace/]);
  const seen = new Set<string>();
  let duplicateCount = 0;
  let missingValues = 0;
  let invalidRows = 0;
  const brands = new Set<string>();
  const products = new Set<string>();
  const platforms = new Set<string>();
  rows.forEach((row) => {
    columns.forEach((column) => { if (row[column] === "" || row[column] == null) missingValues += 1; });
    const review = String(reviewColumn ? row[reviewColumn] || "" : "").toLocaleLowerCase().replace(/\s+/g, " ").trim();
    const product = String(phoneColumn ? row[phoneColumn] || "" : "").trim();
    if (!review || !product) invalidRows += 1;
    const key = `${product.toLocaleLowerCase()}|||${review}`;
    if (review && seen.has(key)) duplicateCount += 1; else if (review) seen.add(key);
    if (brandColumn && row[brandColumn]) brands.add(String(row[brandColumn]).trim());
    if (product) products.add(product);
    if (platformColumn && row[platformColumn]) platforms.add(String(row[platformColumn]).trim());
  });
  const totalCells = Math.max(1, rows.length * Math.max(1, columns.length));
  const duplicateRate = duplicateCount / Math.max(1, rows.length);
  const missingRate = missingValues / totalCells;
  const invalidRate = invalidRows / Math.max(1, rows.length);
  const qualityScore = Math.max(0, Math.min(100, 100 - duplicateRate * 45 - missingRate * 25 - invalidRate * 40));
  const issues = [
    !reviewColumn ? "A review_text column is required for intelligence refresh." : "",
    !phoneColumn ? "A phone_id, phone_name or product column is required." : "",
    duplicateCount ? `${duplicateCount.toLocaleString()} repeated product-review rows should be removed.` : "",
    invalidRows ? `${invalidRows.toLocaleString()} rows are missing product or review evidence.` : "",
    rows.length < 50 ? "Coverage is too small for stable aggregate intelligence." : "",
  ].filter(Boolean);
  return { columns, reviewColumn, phoneColumn, brandColumn, platformColumn, rowCount: rows.length, duplicateCount, missingValues, invalidRows, qualityScore: Number(qualityScore.toFixed(1)), coverage: { brands: brands.size, products: products.size, platforms: platforms.size }, issues, ready: Boolean(reviewColumn && phoneColumn && rows.length >= 50 && qualityScore >= 75) };
}

function publicVersion(row: Record<string, unknown>) {
  return { id: row.id, filename: row.filename, contentType: row.content_type, byteSize: row.byte_size, rowCount: row.row_count, duplicateCount: row.duplicate_count, qualityScore: row.quality_score, status: row.status, createdAt: row.created_at, validation: JSON.parse(String(row.validation_json || "{}")) };
}

export async function GET(request: Request) {
  const owner = ownerId(request);
  if (!owner) return Response.json({ error: "Authentication required" }, { status: 401 });
  try {
    const db = await database();
    const downloadId = new URL(request.url).searchParams.get("download");
    if (downloadId) {
      const row = await db.prepare("SELECT filename, storage_key, content_type FROM dataset_versions WHERE id = ? AND owner_id = ?").bind(downloadId, owner).first<Record<string, unknown>>();
      if (!row || !runtime.UPLOADS) return Response.json({ error: "Dataset version not found" }, { status: 404 });
      const object = await runtime.UPLOADS.get(String(row.storage_key));
      if (!object) return Response.json({ error: "Stored file not found" }, { status: 404 });
      return new Response(object.body, { headers: { "Content-Type": String(row.content_type), "Content-Disposition": `attachment; filename="${String(row.filename).replace(/["\r\n]/g, "")}"` } });
    }
    const result = await db.prepare("SELECT * FROM dataset_versions WHERE owner_id = ? ORDER BY created_at DESC LIMIT 20").bind(owner).all<Record<string, unknown>>();
    return Response.json({ versions: result.results.map(publicVersion) });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Unable to load dataset versions" }, { status: 503 });
  }
}

export async function POST(request: Request) {
  const owner = ownerId(request);
  if (!owner) return Response.json({ error: "Authentication required" }, { status: 401 });
  try {
    if (!runtime.UPLOADS) throw new Error("Dataset storage is unavailable");
    const form = await request.formData();
    const file = form.get("file");
    if (!(file instanceof File)) return Response.json({ error: "Choose a CSV or JSON file" }, { status: 400 });
    if (file.size > MAX_BYTES) return Response.json({ error: "Dataset files must be 8 MB or smaller" }, { status: 413 });
    if (!/\.(csv|json)$/i.test(file.name)) return Response.json({ error: "Only CSV and JSON datasets are supported" }, { status: 415 });
    const text = await file.text();
    let rows: Row[];
    if (/\.json$/i.test(file.name)) {
      const parsed = JSON.parse(text) as Row[] | { reviews?: Row[] };
      rows = Array.isArray(parsed) ? parsed : Array.isArray(parsed.reviews) ? parsed.reviews : [];
    } else rows = parseCsv(text);
    if (!rows.length) return Response.json({ error: "No data rows were found" }, { status: 422 });
    const validation = analyze(rows);
    const id = crypto.randomUUID();
    const createdAt = new Date().toISOString();
    const safeName = file.name.replace(/[^a-zA-Z0-9._-]/g, "-");
    const storageKey = `${owner}/${id}/${safeName}`;
    await runtime.UPLOADS.put(storageKey, await file.arrayBuffer(), { httpMetadata: { contentType: file.type || (/\.json$/i.test(file.name) ? "application/json" : "text/csv") } });
    const db = await database();
    const status = validation.ready ? "Refresh ready" : "Needs attention";
    await db.prepare("INSERT INTO dataset_versions (id, owner_id, filename, storage_key, content_type, byte_size, row_count, duplicate_count, quality_score, status, validation_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)").bind(id, owner, file.name, storageKey, file.type || "text/plain", file.size, validation.rowCount, validation.duplicateCount, validation.qualityScore, status, JSON.stringify(validation), createdAt).run();
    return Response.json({ version: publicVersion({ id, filename: file.name, content_type: file.type || "text/plain", byte_size: file.size, row_count: validation.rowCount, duplicate_count: validation.duplicateCount, quality_score: validation.qualityScore, status, validation_json: JSON.stringify(validation), created_at: createdAt }) }, { status: 201 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dataset validation failed" }, { status: 500 });
  }
}

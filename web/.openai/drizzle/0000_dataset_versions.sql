CREATE TABLE IF NOT EXISTS dataset_versions (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL,
  filename TEXT NOT NULL,
  storage_key TEXT NOT NULL UNIQUE,
  content_type TEXT NOT NULL,
  byte_size INTEGER NOT NULL,
  row_count INTEGER NOT NULL,
  duplicate_count INTEGER NOT NULL,
  quality_score REAL NOT NULL,
  status TEXT NOT NULL,
  validation_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dataset_versions_owner_created
ON dataset_versions(owner_id, created_at DESC);

CREATE TABLE IF NOT EXISTS telemetry_events (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  route TEXT NOT NULL,
  value REAL,
  detail_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telemetry_events_owner_created
ON telemetry_events(owner_id, created_at DESC);

export const datasetVersionsSchema = `
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
)`;

export const datasetVersionsOwnerIndex = `
CREATE INDEX IF NOT EXISTS idx_dataset_versions_owner_created
ON dataset_versions(owner_id, created_at DESC)
`;

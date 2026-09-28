import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("the published evidence snapshot keeps its core reliability contract", async () => {
  const snapshot = JSON.parse(await read("app/data/platform-data.json"));
  const reviews = JSON.parse(await read("public/data/reviews.json"));
  assert.equal(snapshot.overview.metrics.reviews, 3031);
  assert.equal(snapshot.overview.metrics.usable_reviews, 2813);
  assert.equal(snapshot.overview.metrics.brands, 14);
  assert.equal(snapshot.phones.length, 62);
  assert.equal(snapshot.catalog_quality.source_checked_phones, 62);
  assert.equal(snapshot.catalog_quality.awaiting_verification, 0);
  assert.equal(snapshot.finder.overall.length, 51);
  assert.ok(snapshot.phones.every((phone) => phone.spec_source_url && phone.verified_spec_fields.length > 0));
  assert.equal(snapshot.phones.find((phone) => phone.phone_id === "PH027")?.charging_w, 15);
  assert.equal(snapshot.phones.filter((phone) => phone.launch_price != null).length, 62);
  assert.equal(snapshot.phones.filter((phone) => phone.amazon_price != null).length, 52);
  assert.equal(snapshot.phones.filter((phone) => phone.flipkart_price != null).length, 58);
  const pilot = snapshot.phones.filter((phone) => phone.phone_id.startsWith("PHONE-"));
  assert.equal(pilot.length, 5);
  assert.ok(pilot.every((phone) => phone.review_count === 0 && phone.launch_date.startsWith("2026-") && phone.launch_price <= 30000));
  assert.ok(pilot.every((phone) => /^\/phone-images\/[a-z0-9-]+\.webp$/.test(phone.image_url)));
  assert.equal(snapshot.phones.find((phone) => phone.phone_name === "Realme 16x 5G")?.refresh_rate, 144);
  assert.equal(snapshot.phones.find((phone) => phone.phone_id === "PH027")?.best_price, 14859);
  assert.equal(reviews.length, 2813);
  const brands = new Set(reviews.map((review) => review.brand.toLocaleLowerCase().trim()));
  assert.equal(brands.size, 14);
  assert.ok(reviews.every((review) => review.review_id && review.review_text && Array.isArray(review.aspects)));
});

test("navigation, accessibility, loading and failure states are present", async () => {
  const [shell, css, loading, error, notFound] = await Promise.all([read("app/components/PlatformShell.tsx"), read("app/globals.css"), read("app/loading.tsx"), read("app/error.tsx"), read("app/not-found.tsx")]);
  assert.doesNotMatch(shell, /\["Data", "\/data", "08"\]/);
  assert.doesNotMatch(shell, /> Private</);
  assert.match(shell, /62 devices/);
  assert.match(shell, /Skip to workspace/);
  assert.match(shell, /lazy\(\(\) => import/);
  assert.match(css, /prefers-reduced-motion/);
  assert.match(css, /:focus-visible/);
  assert.match(css, /caret-color: transparent/);
  assert.match(css, /input, textarea, \[contenteditable="true"\].*cursor: text/);
  assert.match(loading, /aria-live="polite"/);
  assert.match(error, /Your data has not been changed/);
  assert.match(notFound, /Workspace not found/);
});

test("intelligence includes interactive diagnostics and corpus relationships", async () => {
  const intelligence = await read("app/components/IntelligenceWorkspace.tsx");
  for (const feature of ["DecisionMap", "RiskMatrix", "ThemeConnections", "ConfidenceWatch"]) assert.match(intelligence, new RegExp(feature));
  assert.match(intelligence, /fetch\("\/data\/reviews.json"\)/);
  assert.match(intelligence, /themes that occur together inside the same source review/);
});

test("copilot keeps context, retrieves the review corpus and exposes citations", async () => {
  const copilot = await read("app/components/IntelligenceCopilot.tsx");
  assert.match(copilot, /Context retained/);
  assert.match(copilot, /Source evidence/);
  assert.match(copilot, /Unsupported claims are withheld/);
  assert.match(copilot, /evidenceFor\(reviews/);
  assert.match(copilot, /Compare Samsung and Motorola/);
});

test("dataset versions stay local-only and use quality gates", async () => {
  const [hosting, page, route, migration, workspace] = await Promise.all([read(".openai/hosting.json"), read("app/data/page.tsx"), read("app/api/datasets/route.ts"), read(".openai/drizzle/0000_dataset_versions.sql"), read("app/components/DataWorkspace.tsx")]);
  assert.deepEqual(JSON.parse(hosting), { project_id: "appgprj_6a833486a9908191b5086a778de3b16e", d1: "DB", r2: "UPLOADS" });
  assert.match(page, /notFound\(\)/);
  assert.match(page, /isLocalHost/);
  assert.doesNotMatch(route, /oai-authenticated-user-id/);
  assert.match(route, /local-preview/);
  assert.match(route, /duplicateCount/);
  assert.match(route, /qualityScore/);
  assert.match(migration, /idx_dataset_versions_owner_created/);
  assert.match(workspace, /A staged file never silently changes published conclusions/);
  assert.doesNotMatch(workspace, /Specification verification/);
});

test("product evidence links reach focused reviews without source-check panels", async () => {
  const [products, reviews, intelligence] = await Promise.all([read("app/components/DetailedWorkspaces.tsx"), read("app/components/DetailedReviews.tsx"), read("app/components/IntelligenceWorkspace.tsx")]);
  assert.match(products, /reviewEvidenceUrl\(phone\.phone_id, item\.aspect\)/);
  assert.match(products, /shareUrl\(`\/phones\?phone=/);
  assert.doesNotMatch(products, /VerificationNote/);
  assert.match(reviews, /review\.phone_id !== phoneId/);
  assert.match(reviews, /params\.get\("theme"\)/);
  assert.match(intelligence, /Inspect evidence/);
});

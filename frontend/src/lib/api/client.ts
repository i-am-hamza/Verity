/**
 * Typed API client. Thin wrapper around fetch that:
 *   - prefixes `/api` (so Vite's dev proxy routes to :8000)
 *   - typechecks each response body against the OpenAPI schema
 *   - throws `ApiError` on non-2xx with the body + status, so react-query's
 *     `error` surface stays honest about what failed
 *
 * No ad-hoc fetches live in components; everything that reads server data
 * goes through here so the whole dashboard tracks one contract.
 */
import type { components } from "./schema";

export type LeaderboardOut = components["schemas"]["LeaderboardOut"];
export type LeaderboardRow = components["schemas"]["LeaderboardRow"];
export type LeaderboardMeta = components["schemas"]["LeaderboardMeta"];
export type InstitutionDetail = components["schemas"]["InstitutionDetail"];
export type CoverageOut = components["schemas"]["CoverageOut"];
export type CoverageCell = components["schemas"]["CoverageCell"];
export type CoverageRow = components["schemas"]["CoverageRow"];
export type EvidenceOut = components["schemas"]["EvidenceOut"];
export type EvidenceRow = components["schemas"]["EvidenceRow"];
export type SensitivityOut = components["schemas"]["SensitivityOut"];
export type SensitivityInstitutionRow =
  components["schemas"]["SensitivityInstitutionRow"];
export type TaxonomyVersionView = components["schemas"]["TaxonomyVersionView"];
export type PrecisionCell = components["schemas"]["PrecisionCell"];
export type ReviewSubmit = components["schemas"]["ReviewSubmit"];

// Base URL for every backend request. Local dev leaves VITE_API_URL
// unset and the Vite proxy rewrites "/api/*" to http://localhost:8000
// (see vite.config.ts). Production (Vercel) sets VITE_API_URL to the
// deployed Render URL at build time; Vite inlines the value, so this
// read is static per bundle. Trailing slashes are trimmed so callers
// can concatenate "/dashboard/leaderboard" without doubling the slash.
const RAW_BASE = (import.meta.env.VITE_API_URL ?? "/api") as string;
const BASE = RAW_BASE.replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown, message: string) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit & { signal?: AbortSignal },
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  const text = await res.text();
  const body: unknown = text ? safeJson(text) : null;
  if (!res.ok) {
    throw new ApiError(res.status, body, `API ${res.status} on ${path}`);
  }
  return body as T;
}

function safeJson(raw: string): unknown {
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

// --- endpoints ----------------------------------------------------------

export function getMeta(signal?: AbortSignal): Promise<LeaderboardMeta> {
  return request("/dashboard/meta", { signal });
}

export function getLeaderboard(
  params: { cohort?: string; country?: string; fy?: number | null } = {},
  signal?: AbortSignal,
): Promise<LeaderboardOut> {
  const q = new URLSearchParams();
  if (params.cohort) q.set("cohort", params.cohort);
  if (params.country) q.set("country", params.country);
  if (params.fy !== undefined && params.fy !== null) q.set("fy", String(params.fy));
  const qs = q.toString();
  return request(`/dashboard/leaderboard${qs ? `?${qs}` : ""}`, { signal });
}

export function getInstitution(
  slug: string,
  signal?: AbortSignal,
): Promise<InstitutionDetail> {
  return request(`/dashboard/institutions/${encodeURIComponent(slug)}`, { signal });
}

export function getCoverage(signal?: AbortSignal): Promise<CoverageOut> {
  return request("/dashboard/coverage", { signal });
}

export function getEvidence(
  params: {
    institution_slug?: string;
    fiscal_year?: number;
    pillar?: string;
    category?: string;
    term?: string;
    page?: number;
    page_size?: number;
  } = {},
  signal?: AbortSignal,
): Promise<EvidenceOut> {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") q.set(k, String(v));
  }
  const qs = q.toString();
  return request(`/dashboard/evidence${qs ? `?${qs}` : ""}`, { signal });
}

export function postEvidenceReview(
  payload: ReviewSubmit,
  signal?: AbortSignal,
): Promise<{ ok: boolean }> {
  return request("/dashboard/evidence/review", {
    method: "POST",
    body: JSON.stringify(payload),
    signal,
  });
}

export function getPrecision(
  group: "term" | "category" | "pillar",
  signal?: AbortSignal,
): Promise<PrecisionCell[]> {
  return request(`/dashboard/evidence/precision?group=${group}`, { signal });
}

export function getSensitivity(signal?: AbortSignal): Promise<SensitivityOut> {
  return request("/dashboard/sensitivity", { signal });
}

export function getTaxonomy(signal?: AbortSignal): Promise<TaxonomyVersionView> {
  return request("/dashboard/taxonomy/current", { signal });
}

export function getMethodology(signal?: AbortSignal): Promise<string> {
  return fetch(`${BASE}/dashboard/methodology`, { signal }).then((r) => r.text());
}

export function getBenchmarkStatus(
  signal?: AbortSignal,
): Promise<{ imported: boolean; rows: number; message: string }> {
  return request("/dashboard/benchmark/status", { signal });
}

export function pdfUrl(reportId: number, page?: number): string {
  const base = `${BASE}/dashboard/pdf/${reportId}`;
  return page ? `${base}#page=${page}` : base;
}

export function exportXlsxUrl(): string {
  return `${BASE}/dashboard/export/verity_esg_scores.xlsx`;
}

export function exportCsvUrl(): string {
  return `${BASE}/dashboard/export/verity_esg_scores.csv`;
}

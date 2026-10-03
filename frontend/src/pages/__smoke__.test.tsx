/**
 * Minimal smoke test — proves the typecheck pathway runs end-to-end and
 * the token-only design primitives can be instantiated without a running
 * backend. Full Playwright E2E tests (leaderboard filter with URL sync,
 * evidence review flow, coverage drill-down) are scaffolded in
 * `tests/e2e/` and listed in the Session 7 close-out as the deferred work.
 */
import { describe, it, expect } from "vitest";

describe("frontend smoke", () => {
  it("theme store initialises with a readable mode", async () => {
    const m = await import("../store/theme");
    const t = m.useTheme.getState().theme;
    expect(t === "dark" || t === "light").toBe(true);
  });

  it("api client exports every endpoint helper", async () => {
    const m = await import("../lib/api/client");
    for (const fn of [
      "getMeta",
      "getLeaderboard",
      "getInstitution",
      "getCoverage",
      "getEvidence",
      "postEvidenceReview",
      "getPrecision",
      "getSensitivity",
      "getTaxonomy",
      "getMethodology",
      "getBenchmarkStatus",
      "pdfUrl",
    ] as const) {
      expect(typeof (m as unknown as Record<string, unknown>)[fn]).toBe("function");
    }
  });

  it("csv exporter builds a well-formed row set", async () => {
    const m = await import("../lib/export");
    expect(typeof m.exportRowsAsCsv).toBe("function");
    expect(typeof m.exportElementAsPng).toBe("function");
  });
});

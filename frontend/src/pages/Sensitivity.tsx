import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  CartesianGrid,
  ErrorBar,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { EmptyState, ErrorState, Loading } from "../components/StateViews";
import { exportRowsAsCsv } from "../lib/export";
import {
  getSensitivity,
  type SensitivityInstitutionRow,
} from "../lib/api/client";

/**
 * Rank ticks for the sensitivity scatter: 1, 5, 10, 15, ..., n. Ranks
 * start at 1 (not 0); letting Recharts auto-generate "nice" ticks
 * produces a meaningless 0 label. An explicit tick list anchors the
 * axis at 1 and steps in 5s up to the cohort size.
 */
function rankTicks(n: number): number[] {
  if (n <= 0) return [1];
  const ticks: number[] = [1];
  for (let v = 5; v < n; v += 5) ticks.push(v);
  if (ticks[ticks.length - 1] !== n) ticks.push(n);
  return ticks;
}

const SWITCH_LABEL: Record<string, string> = {
  toc_off: "Table-of-contents off",
  repeat_off: "Repeated-line removal off",
  all_mode: "Matching mode = all",
};

export function SensitivityPage() {
  const q = useQuery({
    queryKey: ["sensitivity"],
    queryFn: ({ signal }) => getSensitivity(signal),
  });
  const [sector, setSector] = useState<"financial" | "non-financial">("financial");
  const [detailOpen, setDetailOpen] = useState(false);

  const rows = useMemo(
    () => (q.data?.rows ?? []).filter((r) => r.sector === sector),
    [q.data, sector],
  );

  const chartData = rows.map((r) => ({
    baseline: r.baseline_rank,
    median: r.jitter_median_rank,
    width: r.jitter_p95_rank - r.jitter_p5_rank,
    slug: r.slug,
    error: [
      r.jitter_median_rank - r.jitter_p5_rank,
      r.jitter_p95_rank - r.jitter_median_rank,
    ],
    years: r.years_covered,
    single_year: r.years_covered === 1,
  }));

  if (q.isLoading) return <Loading label="Loading sensitivity..." />;
  if (q.isError) {
    return (
      <ErrorState
        message="Could not load sensitivity data."
        detail={(q.error as Error).message}
      />
    );
  }
  if (!q.data) return <EmptyState title="Sensitivity analysis hasn't run yet." />;

  const data = q.data;
  const sectorCount = rows.length;
  const stableCount = rows.filter((r) => r.jitter_interval_width <= 1).length;

  return (
    <section className="flex flex-col gap-6">
      <header>
        <h1 className="font-heading text-2xl font-semibold tracking-tight">
          Rank-stability
        </h1>
        <p className="mt-1 text-sm text-text-muted">
          How much within-sector rankings would move under weight jitter,
          equal weights, and the three documented pipeline-switch tests.
        </p>
      </header>

      {/*
        Headline: Kendall tau for both sectors, surfaced as big stat
        callouts rather than buried in a paragraph. "Highly stable" copy
        is a plain-English gloss; the real numbers next to it are the
        auditable claim.
      */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <StatCard
          sector="Financial sector"
          median={data.kendall_fin_median}
          p5={data.kendall_fin_p5}
          p95={data.kendall_fin_p95}
        />
        <StatCard
          sector="Non-financial sector"
          median={data.kendall_non_fin_median}
          p5={data.kendall_non_fin_p5}
          p95={data.kendall_non_fin_p95}
        />
      </div>

      <p className="text-sm text-text-muted">
        Both sectors show{" "}
        <span className="font-semibold text-text">
          Kendall tau &gt; 0.97
        </span>{" "}
        under 1,000 weight-jitter draws of U(0.8, 1.2) — rankings move
        very little when term weights are perturbed within +/- 20 %.
      </p>

      {/*
        Switch-test summary table: the four alternate configurations
        (equal weights + three documented switches) in one place with
        plain Spearman numbers. Rendered as a real styled table using
        the dashboard's token colours, not a markdown pipe table.
      */}
      <section className="rounded-md border border-border bg-surface p-4">
        <h2 className="font-heading text-base font-semibold">Switch tests</h2>
        <p className="mt-1 text-xs text-text-muted">
          Rank correlation (Spearman) between baseline and each
          alternate configuration. 1.000 means every rank is unchanged.
        </p>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[480px] text-sm tabular">
            <thead>
              <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
                <th className="py-2 pr-3 text-left">Configuration</th>
                <th className="py-2 px-3 text-right">Financial</th>
                <th className="py-2 pl-3 text-right">Non-financial</th>
              </tr>
            </thead>
            <tbody>
              <SwitchRow
                label="Equal weights (all term + category weights = 1.0)"
                fin={data.equal_spearman_fin}
                non_fin={data.equal_spearman_non_fin}
              />
              {Object.entries(data.switch_summary).map(([k, v]) => (
                <SwitchRow
                  key={k}
                  label={SWITCH_LABEL[k] ?? k}
                  fin={v.spearman_fin ?? 0}
                  non_fin={v.spearman_non_fin ?? 0}
                />
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/*
        Scatter: baseline rank vs jitter median, with 5-95% error bar.
        A point on the diagonal means the jitter leaves rank unchanged;
        single-year institutions are triangles.
      */}
      <section className="rounded-md border border-border bg-surface p-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="font-heading text-base font-semibold">
              Rank movement under jitter
            </h2>
            <p className="mt-1 text-xs text-text-muted">
              Each point is one institution. Error bars show the 5-95%
              rank interval across 1,000 jittered weight draws.
            </p>
          </div>
          <div className="flex items-center gap-2">
            {(["financial", "non-financial"] as const).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setSector(s)}
                className={[
                  "rounded-md border px-3 py-1 text-sm",
                  sector === s
                    ? "border-accent bg-accent/10 text-accent"
                    : "border-border bg-surface text-text-muted hover:text-text",
                ].join(" ")}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-3 text-xs text-text-faint">
          {sectorCount} institutions in {sector} sector — {stableCount}
          {" "}have a jitter interval of 0-1 ranks ("stable").
        </div>
        <div className="mt-3 h-80 sm:h-96">
          <ResponsiveContainer>
            <ScatterChart margin={{ top: 10, right: 24, bottom: 24, left: 24 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                type="number"
                dataKey="baseline"
                name="baseline rank"
                domain={[1, rows.length]}
                ticks={rankTicks(rows.length)}
                interval={0}
                allowDecimals={false}
                allowDataOverflow={false}
                tickFormatter={(v: number) => (v < 1 ? "" : String(v))}
                label={{
                  value: "baseline rank (1 = best)",
                  position: "insideBottom",
                  offset: -10,
                }}
              />
              <YAxis
                type="number"
                dataKey="median"
                name="jitter median"
                domain={[1, rows.length]}
                ticks={rankTicks(rows.length)}
                interval={0}
                allowDecimals={false}
                allowDataOverflow={false}
                tickFormatter={(v: number) => (v < 1 ? "" : String(v))}
                label={{
                  value: "jitter median (1 = best)",
                  angle: -90,
                  position: "insideLeft",
                }}
              />
              <ReferenceLine
                segment={[
                  { x: 1, y: 1 },
                  { x: rows.length, y: rows.length },
                ]}
                stroke="rgb(var(--border))"
                strokeDasharray="4 2"
                label={{
                  value: "no rank change",
                  position: "insideTopRight",
                  fill: "rgb(var(--text-faint))",
                  fontSize: 10,
                }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.[0]) return null;
                  const p = payload[0].payload as (typeof chartData)[number];
                  return (
                    <div className="rounded-md border border-border bg-surface p-2 text-xs shadow-pop">
                      <div className="font-mono text-text">{p.slug}</div>
                      <div className="text-text-muted">
                        baseline {p.baseline} · median {p.median}
                      </div>
                      <div className="text-text-muted">
                        interval width {p.width}
                      </div>
                      <div className="text-text-faint">
                        {p.years}-year coverage
                      </div>
                    </div>
                  );
                }}
              />
              <Scatter
                data={chartData.filter((d) => !d.single_year)}
                fill="rgb(var(--accent))"
                shape="circle"
                name="multi-year coverage"
              >
                <ErrorBar
                  dataKey="error"
                  width={6}
                  stroke="rgb(var(--accent))"
                />
              </Scatter>
              <Scatter
                data={chartData.filter((d) => d.single_year)}
                fill="rgb(var(--warn))"
                shape="triangle"
                name="single-year coverage"
              >
                <ErrorBar dataKey="error" width={6} stroke="rgb(var(--warn))" />
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/*
        Per-institution detail: hidden by default behind a <details>
        toggle so a reader scrolling the page doesn't have to swipe past
        two dozen rows to reach anything else. Expanding reveals the
        full jitter + per-switch table for every institution in the
        currently selected sector.
      */}
      <section className="rounded-md border border-border bg-surface">
        <details
          open={detailOpen}
          onToggle={(e) => setDetailOpen((e.target as HTMLDetailsElement).open)}
          className="group"
        >
          <summary className="flex cursor-pointer items-center justify-between gap-3 px-4 py-3 text-sm text-text-muted hover:text-text">
            <span>
              <span className="font-heading font-semibold text-text">
                Per-institution rank stability
              </span>{" "}
              <span className="text-xs text-text-faint">
                ({sectorCount} rows in {sector} — click to{" "}
                {detailOpen ? "collapse" : "expand"})
              </span>
            </span>
            <span
              aria-hidden="true"
              className="inline-block text-xs text-text-faint transition-transform group-open:rotate-180"
            >
              ▾
            </span>
          </summary>
          <div className="border-t border-border px-2 py-3 sm:px-4">
            <div className="mb-3 flex flex-wrap justify-end gap-2">
              <button
                type="button"
                onClick={() =>
                  exportRowsAsCsv(
                    rows.map((r) => ({
                      slug: r.slug,
                      sector: r.sector,
                      years_covered: r.years_covered,
                      baseline_rank: r.baseline_rank,
                      jitter_median_rank: r.jitter_median_rank,
                      jitter_p5_rank: r.jitter_p5_rank,
                      jitter_p95_rank: r.jitter_p95_rank,
                      jitter_interval_width: r.jitter_interval_width,
                      equal_weights_rank: r.equal_weights_rank,
                      toc_off_rank: r.toc_off_rank,
                      repeat_off_rank: r.repeat_off_rank,
                      all_mode_rank: r.all_mode_rank,
                      flag_single_year_high_volatility:
                        r.flag_single_year_high_volatility ? "YES" : "",
                    })),
                    `sensitivity-${sector}.csv`,
                  )
                }
                className="rounded-md border border-border bg-surface px-3 py-1 text-xs text-text-muted hover:text-text"
              >
                Export CSV
              </button>
            </div>
            <JitterTable rows={rows} />
          </div>
        </details>
      </section>

      {/*
        Author-prose summary at the end — the generated SENSITIVITY_SUMMARY.md,
        rendered with remark-gfm. The structured tables above are the
        primary surface, so the per-institution rank-stability sections
        inside the markdown would be a duplicate of the collapsible
        detail block above. Strip them out before rendering so the
        prose section is just the headline interpretation + the switch-
        test prose, not another copy of the same 42 rows.
      */}
      <section className="rounded-md border border-border bg-surface p-4">
        <h2 className="font-heading text-base font-semibold">
          Narrative summary
        </h2>
        <article className="prose prose-sm mt-2 max-w-none text-text prose-headings:text-text prose-strong:text-text prose-a:text-accent dark:prose-invert">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {stripPerInstitutionTables(data.summary_markdown) ||
              "_No summary available._"}
          </ReactMarkdown>
        </article>
      </section>
    </section>
  );
}

function StatCard({
  sector,
  median,
  p5,
  p95,
}: {
  sector: string;
  median: number;
  p5: number;
  p95: number;
}) {
  const intervalText =
    p5 > 0 && p95 > 0 ? `[${p5.toFixed(3)}, ${p95.toFixed(3)}]` : "—";
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <div className="text-xs uppercase tracking-wide text-text-muted">
        {sector} · Kendall tau
      </div>
      <div className="mt-2 font-heading text-3xl font-semibold tabular text-text sm:text-4xl">
        {median.toFixed(3)}
      </div>
      <div className="mt-2 text-xs text-text-faint">
        5-95% interval {intervalText}
      </div>
    </div>
  );
}

function SwitchRow({
  label,
  fin,
  non_fin,
}: {
  label: string;
  fin: number;
  non_fin: number;
}) {
  return (
    <tr className="border-b border-border last:border-b-0">
      <td className="py-2 pr-3 text-left text-text">{label}</td>
      <td className="py-2 px-3 text-right tabular text-text">
        {fin.toFixed(3)}
      </td>
      <td className="py-2 pl-3 text-right tabular text-text">
        {non_fin.toFixed(3)}
      </td>
    </tr>
  );
}

function JitterTable({ rows }: { rows: SensitivityInstitutionRow[] }) {
  if (rows.length === 0) {
    return (
      <p className="px-2 text-sm text-text-muted">
        No institutions in this sector.
      </p>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-sm tabular [&_td]:py-1.5 [&_th]:py-2 [&_th:first-child]:sticky [&_th:first-child]:left-0 [&_th:first-child]:bg-surface [&_td:first-child]:sticky [&_td:first-child]:left-0 [&_td:first-child]:bg-surface">
        <thead>
          <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
            <th className="px-2 text-left">Institution</th>
            <th className="px-2 text-right">Years</th>
            <th className="px-2 text-right">Baseline</th>
            <th className="px-2 text-right">Jitter median</th>
            <th className="px-2 text-right">5-95% interval</th>
            <th className="px-2 text-right">Equal wts</th>
            <th className="px-2 text-right">toc_off</th>
            <th className="px-2 text-right">repeat_off</th>
            <th className="px-2 text-right">all_mode</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.slug} className="border-b border-border last:border-b-0">
              <td className="px-2 text-left font-mono text-xs text-text-muted">
                {r.slug}
                {r.flag_single_year_high_volatility ? (
                  <span className="ml-1 rounded-sm bg-warn/15 px-1 text-[10px] font-semibold uppercase text-warn">
                    volatile
                  </span>
                ) : null}
              </td>
              <td className="px-2 text-right">{r.years_covered}</td>
              <td className="px-2 text-right text-text">{r.baseline_rank}</td>
              <td className="px-2 text-right text-text">{r.jitter_median_rank}</td>
              <td className="px-2 text-right text-text">
                [{r.jitter_p5_rank}, {r.jitter_p95_rank}]
              </td>
              <td className="px-2 text-right text-text-muted">
                {diffCell(r.baseline_rank, r.equal_weights_rank)}
              </td>
              <td className="px-2 text-right text-text-muted">
                {diffCell(r.baseline_rank, r.toc_off_rank)}
              </td>
              <td className="px-2 text-right text-text-muted">
                {diffCell(r.baseline_rank, r.repeat_off_rank)}
              </td>
              <td className="px-2 text-right text-text-muted">
                {diffCell(r.baseline_rank, r.all_mode_rank)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function diffCell(base: number, now: number): string {
  if (base === now) return `${now} (0)`;
  const d = now - base;
  return `${now} (${d > 0 ? "+" : ""}${d})`;
}

/**
 * The generated SENSITIVITY_SUMMARY.md includes per-sector pipe tables
 * under `### Financial — per-institution rank stability` and `###
 * Non-financial — per-institution rank stability` headings. We render
 * the same data as a styled HTML table in the collapsible detail block
 * above, so repeating it here is noise. Drop both subsections (header
 * + table body) wholesale.
 */
function stripPerInstitutionTables(md: string): string {
  if (!md) return md;
  // First try: match from the subsection header up to the next header.
  // If the subsection runs to end-of-file, the fallback regex catches it.
  const UNTIL_NEXT_HEADER =
    /^### (?:Financial|Non-financial)[^\n]*per-institution rank stability[\s\S]*?(?=\n#{2,3} )/gm;
  const UNTIL_EOF =
    /^### (?:Financial|Non-financial)[^\n]*per-institution rank stability[\s\S]*$/gm;
  return md
    .replace(UNTIL_NEXT_HEADER, "")
    .replace(UNTIL_EOF, "")
    .replace(/\n{3,}/g, "\n\n");
}

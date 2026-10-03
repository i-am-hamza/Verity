import { useQuery } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  ScatterChart,
  Scatter,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  ErrorBar,
} from "recharts";

import { getSensitivity } from "../lib/api/client";
import { EmptyState, ErrorState, Loading } from "../components/StateViews";
import { exportRowsAsCsv } from "../lib/export";

/**
 * Rank ticks for the sensitivity scatter: 1, 5, 10, 15, …, n. Ranks start
 * at 1 (not 0), so letting Recharts auto-generate "nice" ticks produces a
 * meaningless 0 label. An explicit tick list anchors the axis at 1 and
 * steps in 5s up to the cohort size.
 */
function rankTicks(n: number): number[] {
  if (n <= 0) return [1];
  const ticks: number[] = [1];
  for (let v = 5; v < n; v += 5) ticks.push(v);
  if (ticks[ticks.length - 1] !== n) ticks.push(n);
  return ticks;
}

export function SensitivityPage() {
  const q = useQuery({
    queryKey: ["sensitivity"],
    queryFn: ({ signal }) => getSensitivity(signal),
  });
  const [sector, setSector] = useState<"financial" | "non-financial">("financial");

  const rows = useMemo(
    () => (q.data?.rows ?? []).filter((r) => r.sector === sector),
    [q.data, sector],
  );

  const chartData = rows.map((r) => ({
    baseline: r.baseline_rank,
    median: r.jitter_median_rank,
    width: r.jitter_p95_rank - r.jitter_p5_rank,
    slug: r.slug,
    error: [r.jitter_median_rank - r.jitter_p5_rank, r.jitter_p95_rank - r.jitter_median_rank],
    years: r.years_covered,
    single_year: r.years_covered === 1,
  }));

  if (q.isLoading) return <Loading label="Loading sensitivity…" />;
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

  return (
    <section className="flex flex-col gap-5">
      <header>
        <h1 className="font-heading text-2xl font-semibold tracking-tight">
          Rank-stability
        </h1>
        <p className="mt-1 text-sm text-text-muted">
          Baseline rank vs. jitter median with 5-95% rank interval, within sector.
          Switch tests + plain-English findings below.
        </p>
      </header>

      <div className="flex gap-2">
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
                flag_single_year_high_volatility: r.flag_single_year_high_volatility ? "YES" : "",
              })),
              `sensitivity-${sector}.csv`,
            )
          }
          className="ml-auto rounded-md border border-border bg-surface px-3 py-1 text-xs text-text-muted hover:text-text"
        >
          Export CSV
        </button>
      </div>

      <div className="rounded-md border border-border bg-surface p-4">
        <div className="h-96">
          <ResponsiveContainer>
            <ScatterChart margin={{ top: 10, right: 24, bottom: 24, left: 24 }}>
              <CartesianGrid strokeDasharray="3 3" />
              {/* Both axes ascending from 1 (ranks don't start at 0) to the
                  cohort size. Reversed used to make numerically-higher ranks
                  (= worse) appear further out, but it flipped the diagonal
                  interpretation and introduced a bogus 0 tick. Ascending
                  domain [1, n] keeps "jitter median > baseline" above the
                  diagonal (= rank worsened) and vice versa, consistent on
                  both axes. */}
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
                label={{ value: "baseline rank (1 = best)", position: "insideBottom", offset: -10 }}
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
                label={{ value: "jitter median (1 = best)", angle: -90, position: "insideLeft" }}
              />
              <ReferenceLine
                segment={[
                  { x: 1, y: 1 },
                  { x: rows.length, y: rows.length },
                ]}
                stroke="rgb(var(--border))"
                strokeDasharray="4 2"
                label={{ value: "no rank change", position: "insideTopRight", fill: "rgb(var(--text-faint))", fontSize: 10 }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.[0]) return null;
                  const p = payload[0].payload as (typeof chartData)[number];
                  return (
                    <div className="rounded-md border border-border bg-surface p-2 text-xs">
                      <div className="font-mono text-text">{p.slug}</div>
                      <div className="text-text-muted">
                        baseline {p.baseline} · median {p.median}
                      </div>
                      <div className="text-text-muted">interval width {p.width}</div>
                      <div className="text-text-faint">{p.years}-year coverage</div>
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
                <ErrorBar dataKey="error" width={6} stroke="rgb(var(--accent))" />
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
        <figcaption className="mt-2 text-[11px] text-text-faint">
          Points on the diagonal = jitter leaves rank unchanged. Error bars = 5-95%
          interval across 1,000 weight-jitter draws. Triangles mark single-year
          institutions — those scores are inherently less robust regardless of
          jitter.
        </figcaption>
      </div>

      <section className="rounded-md border border-border bg-surface p-4">
        <h2 className="font-heading text-lg font-semibold">Switch tests</h2>
        <div className="mt-3 overflow-x-auto">
        <table className="min-w-[560px] text-sm tabular [&_th:first-child]:sticky [&_th:first-child]:left-0 [&_th:first-child]:bg-surface [&_td:first-child]:sticky [&_td:first-child]:left-0 [&_td:first-child]:bg-surface">
          <thead>
            <tr className="text-xs uppercase tracking-wide text-text-muted">
              <th className="px-2 py-1 text-left">slug</th>
              <th className="px-2 py-1 text-right">baseline</th>
              <th className="px-2 py-1 text-right">equal wts</th>
              <th className="px-2 py-1 text-right">toc_off</th>
              <th className="px-2 py-1 text-right">repeat_off</th>
              <th className="px-2 py-1 text-right">all_mode</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.slug} className="border-t border-border">
                <td className="px-2 py-1 text-left">{r.slug}</td>
                <td className="px-2 py-1 text-right">{r.baseline_rank}</td>
                <td className="px-2 py-1 text-right">{diff(r.baseline_rank, r.equal_weights_rank)}</td>
                <td className="px-2 py-1 text-right">{diff(r.baseline_rank, r.toc_off_rank)}</td>
                <td className="px-2 py-1 text-right">{diff(r.baseline_rank, r.repeat_off_rank)}</td>
                <td className="px-2 py-1 text-right">{diff(r.baseline_rank, r.all_mode_rank)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </section>

      <section className="prose prose-sm max-w-none rounded-md border border-border bg-surface p-4 prose-invert dark:prose-invert">
        <h2 className="font-heading text-lg font-semibold not-prose">Plain-English summary</h2>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {data.summary_markdown || "_No summary available._"}
        </ReactMarkdown>
      </section>
    </section>
  );
}

function diff(base: number, now: number): string {
  if (base === now) return `${now} (±0)`;
  const d = now - base;
  return `${now} (${d > 0 ? "+" : ""}${d})`;
}

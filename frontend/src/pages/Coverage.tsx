import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { getCoverage, type CoverageCell } from "../lib/api/client";
import { EmptyState, ErrorState, Loading } from "../components/StateViews";
import { exportRowsAsCsv } from "../lib/export";

const CELL_STYLE: Record<string, string> = {
  scored: "bg-env/15 text-env border-env/40",
  needs_review: "bg-warn/15 text-warn border-warn/40",
  gap: "bg-surface-2 text-text-muted border-border",
  not_attempted: "bg-surface text-text-faint border-border",
};

export function CoveragePage() {
  const query = useQuery({ queryKey: ["coverage"], queryFn: ({ signal }) => getCoverage(signal) });
  const [selected, setSelected] = useState<{ slug: string; fy: number; cell: CoverageCell } | null>(null);

  if (query.isLoading) return <Loading label="Loading coverage matrix…" />;
  if (query.isError) {
    return (
      <ErrorState
        message="Could not load coverage data."
        detail={(query.error as Error).message}
      />
    );
  }
  if (!query.data) return <EmptyState title="No coverage data yet." />;
  const data = query.data;

  function exportGapCsv() {
    const rows = data.rows.flatMap((r) =>
      data.fiscal_years
        .filter((fy) => (r.cells[fy]?.status ?? "not_attempted") !== "scored")
        .map((fy) => {
          const c = r.cells[fy];
          return {
            slug: r.slug,
            name: r.name,
            sector: r.sector,
            fiscal_year: fy,
            status: c?.status ?? "not_attempted",
            reason: c?.reason ?? "",
            source: c?.source ?? "",
            sha256_prefix: c?.sha256_prefix ?? "",
          };
        }),
    );
    exportRowsAsCsv(rows, "verity-gap-list.csv");
  }

  return (
    <section className="flex flex-col gap-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-heading text-2xl font-semibold tracking-tight">Coverage</h1>
          <p className="mt-1 text-sm text-text-muted">
            Institution × FY matrix. Click a cell for its source, hash and gap reason.
          </p>
        </div>
        <button
          type="button"
          onClick={exportGapCsv}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export gap list (CSV)
        </button>
      </header>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-text-muted">
        <Legend swatch="scored" label="scored" />
        <Legend swatch="needs_review" label="needs_review" />
        <Legend swatch="gap" label="gap (reason)" />
        <Legend swatch="not_attempted" label="not attempted" />
        <span className="w-full text-xs text-text-faint sm:ml-auto sm:w-auto">
          not covered: {data.unscored_reasons.A_no_file} no file ·{" "}
          {data.unscored_reasons.B_wayback_only_blocked} wayback-only blocked ·{" "}
          {data.unscored_reasons.D_page_threshold} below page threshold
        </span>
      </div>

      {/* 60 × 6 matrix. Two layout modes:
          - Below ~800 px viewport: `min-w-max` + fixed column widths means
            the table is wider than the container, horizontal scroll kicks
            in, the institution column is sticky-left. (Phone / small-tablet
            path. Unchanged from Session 8.)
          - At `min-[800px]:` and up: switch to `table-fixed` + percentage
            widths so the table fills the full container. The institution
            column keeps its sticky positioning but takes 25 % of the
            container; the 6 FY columns share the remaining 75 % evenly
            (12.5 % each). The pixel min/max from the mobile path are
            explicitly lifted (`min-w-0`, `max-w-none`, `w-auto`) because
            Tailwind doesn't automatically retract an earlier breakpoint's
            fixed widths.
          The 800 px threshold is derived from the mobile minimums: a
          220 px institution column + 6 × 88 px FY columns + 2 px border
          + 48 px main-content side padding = 798 px viewport. Below
          that, scroll is necessary; at or above, the columns already fit
          and the empty gap on the right is purely wasted space. */}
      <div className="relative rounded-md border border-border">
        <div className="overflow-x-auto min-[800px]:overflow-visible">
          <table className="min-w-max text-sm min-[800px]:w-full min-[800px]:min-w-full min-[800px]:table-fixed">
            <thead className="bg-surface-2">
              <tr>
                <th
                  scope="col"
                  className="sticky left-0 z-10 w-[160px] min-w-[160px] max-w-[160px] bg-surface-2 px-3 py-3 text-left text-xs uppercase tracking-wide text-text-muted shadow-[2px_0_0_rgb(var(--border))] sm:w-[220px] sm:min-w-[220px] sm:max-w-[220px] sm:px-4 min-[800px]:w-1/4 min-[800px]:min-w-0 min-[800px]:max-w-none"
                >
                  Institution
                </th>
                {data.fiscal_years.map((fy) => (
                  <th
                    key={fy}
                    scope="col"
                    className="min-w-[64px] px-2 py-3 text-center text-xs uppercase tracking-wide text-text-muted sm:min-w-[88px] sm:px-4 min-[800px]:w-[12.5%] min-[800px]:min-w-0"
                  >
                    FY{fy}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row) => (
                <tr key={row.slug} className="border-t border-border">
                  <td className="sticky left-0 z-10 w-[160px] min-w-[160px] max-w-[160px] bg-surface px-3 py-2.5 text-left shadow-[2px_0_0_rgb(var(--border))] sm:w-[220px] sm:min-w-[220px] sm:max-w-[220px] sm:px-4 sm:py-3 min-[800px]:w-1/4 min-[800px]:min-w-0 min-[800px]:max-w-none">
                    <Link
                      to={`/institution/${row.slug}`}
                      className="block truncate text-sm hover:text-accent"
                      title={row.name}
                    >
                      {row.name}
                    </Link>
                    <div className="truncate text-[11px] text-text-faint">
                      {row.sector}
                    </div>
                  </td>
                  {data.fiscal_years.map((fy) => {
                    const cell = row.cells[fy];
                    if (!cell) return <td key={fy} />;
                    const cls = CELL_STYLE[cell.status] ?? "";
                    return (
                      <td key={fy} className="px-2 py-2 text-center sm:px-3 sm:py-2.5 min-[800px]:w-[12.5%]">
                        <button
                          type="button"
                          onClick={() => setSelected({ slug: row.slug, fy, cell })}
                          className={`inline-flex min-h-[32px] w-full items-center justify-center rounded-md border px-2 py-1.5 text-xs font-semibold uppercase sm:min-h-[36px] ${cls}`}
                          title={cell.reason}
                          aria-label={`${row.name} FY${fy}: ${cell.status}. ${cell.reason}`}
                        >
                          {cell.status === "scored" ? "✓" : cell.status === "needs_review" ? "!" : cell.status === "gap" ? "–" : "·"}
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {/* Right-edge scroll affordance: gradient fade shows there's more
            table off-screen. Only visible below the 800 px breakpoint;
            above that the table fills the container so there is nothing
            to scroll to and the gradient would just be visual noise. */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-y-0 right-0 w-8 bg-gradient-to-l from-bg to-transparent sm:w-10 min-[800px]:hidden"
        />
      </div>

      {selected ? (
        <div
          role="dialog"
          aria-modal="true"
          className="rounded-md border border-border bg-surface p-4 shadow-pop"
        >
          <div className="flex justify-between gap-3">
            <div>
              <h3 className="font-heading text-base font-semibold">
                {selected.slug} · FY{selected.fy}
              </h3>
              <p className="mt-1 text-sm text-text-muted">status: {selected.cell.status}</p>
              <p className="text-xs text-text-faint">{selected.cell.reason}</p>
              {selected.cell.source_url ? (
                <a
                  href={selected.cell.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-block break-all text-sm text-accent hover:underline"
                >
                  {selected.cell.source_url}
                </a>
              ) : null}
              {selected.cell.sha256_prefix ? (
                <p className="mt-1 font-mono text-xs text-text-muted">
                  sha256 {selected.cell.sha256_prefix}
                </p>
              ) : null}
            </div>
            <button
              type="button"
              onClick={() => setSelected(null)}
              className="rounded-md border border-border bg-surface px-2 py-1 text-xs text-text-muted hover:text-text"
            >
              close
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function Legend({ swatch, label }: { swatch: keyof typeof CELL_STYLE | string; label: string }) {
  const cls = CELL_STYLE[swatch] ?? "";
  return (
    <span className="inline-flex items-center gap-2">
      {/* Legend swatch sized to match the actual cell border/fill style
          at a readable size (4x4 = 16px). Previously 3x3 (12px) which
          was easy to miss. */}
      <span className={`inline-block h-4 w-4 rounded-sm border-2 ${cls}`} />
      <span className="text-sm">{label}</span>
    </span>
  );
}

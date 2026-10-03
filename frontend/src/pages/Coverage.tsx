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

      <div className="flex flex-wrap gap-4 text-xs text-text-muted">
        <Legend swatch="scored" label="scored" />
        <Legend swatch="needs_review" label="needs_review" />
        <Legend swatch="gap" label="gap (reason)" />
        <Legend swatch="not_attempted" label="not attempted" />
        <span className="ml-auto text-text-faint">
          not covered: {data.unscored_reasons.A_no_file} no file ·{" "}
          {data.unscored_reasons.B_wayback_only_blocked} wayback-only blocked ·{" "}
          {data.unscored_reasons.D_page_threshold} below page threshold
        </span>
      </div>

      <div className="overflow-x-auto rounded-md border border-border">
        <table className="min-w-full text-sm">
          <thead className="bg-surface-2">
            <tr>
              <th scope="col" className="px-3 py-2 text-left text-xs uppercase tracking-wide text-text-muted">
                Institution
              </th>
              {data.fiscal_years.map((fy) => (
                <th key={fy} scope="col" className="px-3 py-2 text-center text-xs uppercase tracking-wide text-text-muted">
                  FY{fy}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row) => (
              <tr key={row.slug} className="border-t border-border">
                <td className="px-3 py-2 text-left">
                  <Link to={`/institution/${row.slug}`} className="hover:text-accent">
                    {row.name}
                  </Link>
                  <div className="text-[11px] text-text-faint">
                    {row.sector}
                  </div>
                </td>
                {data.fiscal_years.map((fy) => {
                  const cell = row.cells[fy];
                  if (!cell) return <td key={fy} />;
                  const cls = CELL_STYLE[cell.status] ?? "";
                  return (
                    <td key={fy} className="px-1 py-1 text-center">
                      <button
                        type="button"
                        onClick={() => setSelected({ slug: row.slug, fy, cell })}
                        className={`inline-flex w-full items-center justify-center rounded-md border px-2 py-1 text-[11px] font-medium uppercase ${cls}`}
                        title={cell.reason}
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
      <span className={`inline-block h-3 w-3 rounded-sm border ${cls}`} />
      {label}
    </span>
  );
}

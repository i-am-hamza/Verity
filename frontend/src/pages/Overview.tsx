import { useMemo, useState, type ReactElement } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import {
  getLeaderboard,
  type LeaderboardRow,
} from "../lib/api/client";
import { EmptyState, ErrorState, Loading } from "../components/StateViews";
import { useUrlNumber, useUrlState } from "../hooks/useUrlState";
import { exportRowsAsCsv } from "../lib/export";

type SortKey =
  | "rank_within_sector"
  | "rank_overall"
  | "mean_composite"
  | "env"
  | "soc"
  | "gov"
  | "name"
  | "country"
  | "years_count";

const COHORT_OPTIONS = ["All", "Financial", "Non-financial"] as const;
const FY_OPTIONS = [null, 2020, 2021, 2022, 2023, 2024, 2025] as const;

export function OverviewPage() {
  const [cohort, setCohort] = useUrlState<string>("cohort", "Financial");
  const [country, setCountry] = useUrlState<string>("country", "");
  const [fy, setFy] = useUrlNumber("fy", null);
  const [sort, setSort] = useState<SortKey>("rank_within_sector");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const query = useQuery({
    queryKey: ["leaderboard", cohort, country, fy],
    queryFn: ({ signal }) =>
      getLeaderboard({ cohort, country: country || undefined, fy }, signal),
  });

  const countries = useMemo(() => {
    if (!query.data) return [];
    return Array.from(new Set(query.data.rows.map((r) => r.country))).sort();
  }, [query.data]);

  const sortedRows = useMemo(() => {
    if (!query.data) return [];
    const rows = [...query.data.rows];
    rows.sort((a, b) => {
      let av: string | number = 0;
      let bv: string | number = 0;
      switch (sort) {
        case "name":
          av = a.name;
          bv = b.name;
          break;
        case "country":
          av = a.country;
          bv = b.country;
          break;
        case "years_count":
          av = a.years_covered.length;
          bv = b.years_covered.length;
          break;
        default:
          av = a[sort] as number;
          bv = b[sort] as number;
          break;
      }
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return rows;
  }, [query.data, sort, sortDir]);

  function toggleSort(k: SortKey) {
    if (sort === k) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else {
      setSort(k);
      // Default ascending for rank columns, descending for score columns.
      setSortDir(k.startsWith("rank") || k === "name" || k === "country" ? "asc" : "desc");
    }
  }

  function headerCell(label: string, k: SortKey, align: "left" | "right" = "left") {
    const active = sort === k;
    return (
      <button
        type="button"
        onClick={() => toggleSort(k)}
        className={[
          "flex w-full items-center gap-1 text-xs font-medium uppercase tracking-wide",
          align === "right" ? "justify-end" : "justify-start",
          active ? "text-text" : "text-text-muted hover:text-text",
        ].join(" ")}
      >
        {label}
        {active ? <span aria-hidden>{sortDir === "asc" ? "↑" : "↓"}</span> : null}
      </button>
    );
  }

  function downloadCsv() {
    if (!query.data) return;
    const header =
      `# verity leaderboard | cohort=${cohort} country=${country || "all"} ` +
      `fy=${fy ?? "mean"} | taxonomy=${query.data.meta.taxonomy_version.slice(0, 12)} ` +
      `snapshot=${query.data.meta.data_snapshot_date}`;
    exportRowsAsCsv(
      sortedRows.map((r) => ({
        rank_overall: r.rank_overall,
        rank_within_sector: r.rank_within_sector,
        slug: r.slug,
        name: r.name,
        sector: r.sector,
        country: r.country,
        mean_composite: r.mean_composite,
        env: r.env,
        soc: r.soc,
        gov: r.gov,
        years_covered: r.years_covered.join(";"),
        data_quality_flag: r.data_quality_flag,
      })),
      "verity-leaderboard.csv",
      header,
    );
  }

  const crossSector = cohort === "All" || cohort === "all" || cohort === "";

  return (
    <section className="flex flex-col gap-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-heading text-2xl font-semibold tracking-tight">
            Leaderboard
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            Mean composite within sector · taxonomy sourced from GRI / SASB
            Financial Sector Standard.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={downloadCsv}
            className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
          >
            Export CSV
          </button>
        </div>
      </header>

      {crossSector ? (
        <div className="rounded-md border border-warn/40 bg-warn/5 px-3 py-2 text-xs">
          <strong className="text-warn">Cross-sector comparison:</strong>{" "}
          the taxonomy is finance-oriented. Read with care — within-sector rank
          is the safer comparison.
        </div>
      ) : null}

      <div className="flex flex-wrap gap-3 rounded-md border border-border bg-surface p-3">
        <label className="flex items-center gap-2 text-xs text-text-muted">
          Cohort
          <select
            value={cohort}
            onChange={(e) => setCohort(e.target.value)}
            className="rounded-md border border-border bg-surface-2 px-2 py-1 text-sm text-text"
          >
            {COHORT_OPTIONS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 text-xs text-text-muted">
          Country
          <select
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            className="rounded-md border border-border bg-surface-2 px-2 py-1 text-sm text-text"
          >
            <option value="">All</option>
            {countries.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 text-xs text-text-muted">
          Fiscal year
          <select
            value={fy === null ? "" : String(fy)}
            onChange={(e) => setFy(e.target.value === "" ? null : Number(e.target.value))}
            className="rounded-md border border-border bg-surface-2 px-2 py-1 text-sm text-text"
          >
            {FY_OPTIONS.map((opt) => (
              <option key={opt ?? "mean"} value={opt === null ? "" : String(opt)}>
                {opt === null ? "Mean" : String(opt)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {query.isLoading ? (
        <Loading label="Loading leaderboard…" />
      ) : query.isError ? (
        <ErrorState
          message="Could not load the leaderboard."
          detail={(query.error as Error | undefined)?.message}
        />
      ) : query.data && query.data.rows.length === 0 ? (
        <EmptyState title="No institutions match this filter." />
      ) : query.data ? (
        <LeaderboardTable
          rows={sortedRows}
          headerCell={headerCell}
          totalFromMeta={query.data.rows.length}
        />
      ) : null}
    </section>
  );
}

function LeaderboardTable({
  rows,
  headerCell,
  totalFromMeta,
}: {
  rows: LeaderboardRow[];
  headerCell: (label: string, k: SortKey, align?: "left" | "right") => ReactElement;
  totalFromMeta: number;
}) {
  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <table className="min-w-full border-collapse text-sm">
        <caption className="sr-only">
          Leaderboard of {totalFromMeta} institutions ranked by composite ESG disclosure
          density.
        </caption>
        <thead className="bg-surface-2">
          <tr>
            <th scope="col" className="px-3 py-2 text-left">
              {headerCell("Sector rk", "rank_within_sector", "left")}
            </th>
            <th scope="col" className="px-3 py-2 text-left">
              {headerCell("Overall rk", "rank_overall", "left")}
            </th>
            <th scope="col" className="px-3 py-2 text-left">
              {headerCell("Institution", "name", "left")}
            </th>
            <th scope="col" className="px-3 py-2 text-left">
              {headerCell("Country", "country", "left")}
            </th>
            <th scope="col" className="px-3 py-2 text-right">
              {headerCell("Composite", "mean_composite", "right")}
            </th>
            <th scope="col" className="px-3 py-2 text-right">
              {headerCell("E", "env", "right")}
            </th>
            <th scope="col" className="px-3 py-2 text-right">
              {headerCell("S", "soc", "right")}
            </th>
            <th scope="col" className="px-3 py-2 text-right">
              {headerCell("G", "gov", "right")}
            </th>
            <th scope="col" className="px-3 py-2 text-left">
              {headerCell("Years", "years_count", "left")}
            </th>
          </tr>
        </thead>
        <tbody className="tabular">
          {rows.map((r) => (
            <tr
              key={r.slug}
              className="border-t border-border transition-colors hover:bg-surface-2/60"
            >
              <td className="px-3 py-2 text-left">{r.rank_within_sector}</td>
              <td className="px-3 py-2 text-left text-text-muted">{r.rank_overall}</td>
              <td className="px-3 py-2 text-left">
                <Link
                  to={`/institution/${r.slug}`}
                  className="font-medium hover:text-accent"
                >
                  {r.name}
                </Link>
                {r.data_quality_flag ? (
                  <span
                    className="ml-1 inline-flex items-center rounded-full border border-warn/40 bg-warn/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-warn"
                    title={r.data_quality_reason}
                  >
                    * flag
                  </span>
                ) : null}
                <div className="text-xs text-text-faint">
                  {r.sector === "financial" ? "Financial" : "Non-financial"}
                  {r.industry ? ` · ${r.industry}` : ""}
                </div>
              </td>
              <td className="px-3 py-2 text-left text-text-muted">{r.country}</td>
              <td className="px-3 py-2 text-right">{r.mean_composite.toFixed(3)}</td>
              <PillarCell value={r.env} pillar="env" />
              <PillarCell value={r.soc} pillar="soc" />
              <PillarCell value={r.gov} pillar="gov" />
              <td className="px-3 py-2 text-left text-text-muted">
                {r.years_covered.length}
                <span className="text-text-faint"> / 6</span>
                <div className="text-[11px] text-text-faint">
                  {r.years_covered.map((y) => String(y).slice(2)).join(", ")}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PillarCell({ value, pillar }: { value: number; pillar: "env" | "soc" | "gov" }) {
  // All three pillars sized against the same visual max for cross-row
  // comparability. 10 is a safe ceiling given tonight's composite range (0-8).
  const max = 10;
  const pct = Math.min(100, (value / max) * 100);
  return (
    <td className="px-3 py-2 text-right align-middle">
      <div className="flex items-center justify-end gap-2">
        <div
          aria-hidden
          className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-2"
        >
          <div
            className={`h-full bg-${pillar}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="tabular w-10 text-right">{value.toFixed(2)}</span>
      </div>
    </td>
  );
}

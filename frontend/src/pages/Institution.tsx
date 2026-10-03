import { useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";

import { getInstitution, pdfUrl, type InstitutionDetail } from "../lib/api/client";
import { EmptyState, ErrorState, Loading } from "../components/StateViews";
import { exportElementAsPng, exportRowsAsCsv } from "../lib/export";

export function InstitutionPage() {
  const { slug = "" } = useParams();
  const query = useQuery({
    queryKey: ["institution", slug],
    enabled: slug.length > 0,
    queryFn: ({ signal }) => getInstitution(slug, signal),
  });

  if (query.isLoading) return <Loading label="Loading institution…" />;
  if (query.isError) {
    return (
      <ErrorState
        message="Could not load institution details."
        detail={(query.error as Error).message}
      />
    );
  }
  if (!query.data) return <EmptyState title="No data for this institution yet." />;

  const inst = query.data;

  return (
    <section className="flex flex-col gap-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-wide text-text-muted">
            {inst.sector === "financial" ? "Financial" : "Non-financial"}
            {inst.industry ? ` · ${inst.industry}` : ""}
          </div>
          <h1 className="mt-1 font-heading text-3xl font-semibold tracking-tight">
            {inst.name}
          </h1>
          <div className="mt-1 flex flex-wrap gap-x-5 gap-y-1 text-sm text-text-muted">
            <span>{inst.country}</span>
            {inst.ticker ? <span>Ticker {inst.ticker}</span> : null}
            {inst.market_cap_usd ? (
              <span>
                Market cap{" "}
                <span className="tabular">
                  ${(inst.market_cap_usd / 1_000_000_000).toFixed(2)}B
                </span>{" "}
                <span className="text-text-faint">
                  as of {inst.market_cap_date ?? "—"}
                </span>
              </span>
            ) : null}
          </div>
        </div>
        <Link
          to={`/evidence?institution_slug=${inst.slug}`}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          View evidence →
        </Link>
      </header>

      {inst.data_quality_flag ? (
        <div
          role="alert"
          className="rounded-md border border-warn/40 bg-warn/5 p-3 text-sm"
        >
          <div className="font-semibold text-warn">
            Data-quality flag: {inst.data_quality_flag}
          </div>
          <p className="mt-1 text-text-muted">{inst.data_quality_reason}</p>
        </div>
      ) : null}

      {/* Charts stack on mobile; two-up from lg (1024px). */}
      <div className="grid gap-4 lg:grid-cols-2">
        <PillarRadar inst={inst} />
        <PillarTrend inst={inst} />
      </div>

      <CategoryBreakdown inst={inst} />

      <ReportList inst={inst} />
    </section>
  );
}

function PillarRadar({ inst }: { inst: InstitutionDetail }) {
  // The two-year compare lives entirely in UI state; the data is already
  // in `inst.reports`.
  const [fyA, setFyA] = useState<number | "">(inst.reports.at(-1)?.fiscal_year ?? "");
  const [fyB, setFyB] = useState<number | "">(
    inst.reports.length > 1 ? inst.reports.at(-2)?.fiscal_year ?? "" : "",
  );
  const ref = useRef<HTMLDivElement>(null);

  const data = useMemo(() => {
    const years = [fyA, fyB].filter((y): y is number => y !== "");
    const chosen = inst.reports.filter((r) => years.includes(r.fiscal_year));
    const pillars = ["Environmental", "Social", "Governance"] as const;
    return pillars.map((pillar) => {
      const row: Record<string, string | number> = { pillar };
      for (const r of chosen) {
        row[String(r.fiscal_year)] =
          pillar === "Environmental" ? r.env : pillar === "Social" ? r.soc : r.gov;
      }
      return row;
    });
  }, [inst, fyA, fyB]);

  return (
    <div ref={ref} className="rounded-md border border-border bg-surface p-4">
      <div className="flex items-center justify-between gap-2">
        <h2 className="font-heading text-lg font-semibold">Pillar profile</h2>
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <FySelect label="A" value={fyA} onChange={setFyA} options={inst.years_covered} />
          <FySelect label="B" value={fyB} onChange={setFyB} options={inst.years_covered} allowEmpty />
          <ExportPng target={ref} filename={`${inst.slug}-radar.png`} />
        </div>
      </div>
      <div className="h-72">
        <ResponsiveContainer>
          <RadarChart data={data} outerRadius="75%">
            <PolarGrid />
            <PolarAngleAxis dataKey="pillar" />
            <PolarRadiusAxis angle={30} />
            {fyA !== "" ? (
              <Radar
                name={String(fyA)}
                dataKey={String(fyA)}
                stroke="rgb(var(--accent))"
                fill="rgb(var(--accent))"
                fillOpacity={0.25}
              />
            ) : null}
            {fyB !== "" ? (
              <Radar
                name={String(fyB)}
                dataKey={String(fyB)}
                stroke="rgb(var(--secondary))"
                fill="rgb(var(--secondary))"
                fillOpacity={0.2}
                strokeDasharray="4 2"
              />
            ) : null}
            <Legend />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="mt-1 text-[11px] text-text-faint">
        Weighted density per 1,000 Latin words · solid = year A, dashed = year B.
      </figcaption>
    </div>
  );
}

function FySelect({
  label,
  value,
  onChange,
  options,
  allowEmpty,
}: {
  label: string;
  value: number | "";
  onChange: (v: number | "") => void;
  options: number[];
  allowEmpty?: boolean;
}) {
  return (
    <label className="flex items-center gap-1">
      {label}
      <select
        value={value === "" ? "" : String(value)}
        onChange={(e) => onChange(e.target.value === "" ? "" : Number(e.target.value))}
        className="rounded-md border border-border bg-surface-2 px-2 py-1 text-sm text-text"
      >
        {allowEmpty ? <option value="">—</option> : null}
        {options.map((y) => (
          <option key={y} value={String(y)}>
            {y}
          </option>
        ))}
      </select>
    </label>
  );
}

function PillarTrend({ inst }: { inst: InstitutionDetail }) {
  const ref = useRef<HTMLDivElement>(null);
  const data = inst.reports.map((r) => ({
    fy: r.fiscal_year,
    Environmental: r.env,
    Social: r.soc,
    Governance: r.gov,
  }));
  return (
    <div ref={ref} className="rounded-md border border-border bg-surface p-4">
      <div className="flex items-center justify-between gap-2">
        <h2 className="font-heading text-lg font-semibold">Pillar trend</h2>
        <ExportPng target={ref} filename={`${inst.slug}-trend.png`} />
      </div>
      <div className="h-72">
        <ResponsiveContainer>
          <LineChart data={data} margin={{ left: 0, right: 20, top: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="fy" />
            <YAxis label={{ value: "density /1000 words", angle: -90, position: "insideLeft" }} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="Environmental"
              stroke="rgb(var(--env))"
              strokeWidth={2}
              dot={{ r: 3 }}
            />
            <Line
              type="monotone"
              dataKey="Social"
              stroke="rgb(var(--soc))"
              strokeWidth={2}
              strokeDasharray="4 2"
              dot={{ r: 3 }}
            />
            <Line
              type="monotone"
              dataKey="Governance"
              stroke="rgb(var(--gov))"
              strokeWidth={2}
              strokeDasharray="6 3"
              dot={{ r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="mt-1 text-[11px] text-text-faint">
        Pillar colour pairs with a line-style marker so the chart remains readable
        in grayscale.
      </figcaption>
    </div>
  );
}

function CategoryBreakdown({ inst }: { inst: InstitutionDetail }) {
  const years = Object.keys(inst.category_breakdown).sort();
  if (years.length === 0) {
    return <EmptyState title="No category breakdown yet for this institution." />;
  }
  // Build a per-category series across years so we can print simple inline bars.
  const categories = Array.from(
    new Set(years.flatMap((y) => Object.keys(inst.category_breakdown[y] ?? {}))),
  ).sort();
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <h2 className="font-heading text-lg font-semibold">Category densities</h2>
      <div className="mt-3 overflow-x-auto">
        <table className="min-w-full text-sm tabular [&_th:first-child]:sticky [&_th:first-child]:left-0 [&_th:first-child]:bg-surface [&_td:first-child]:sticky [&_td:first-child]:left-0 [&_td:first-child]:bg-surface">
          <thead>
            <tr className="text-xs uppercase tracking-wide text-text-muted">
              <th className="px-2 py-1 text-left">Category</th>
              {years.map((y) => (
                <th key={y} className="px-2 py-1 text-right">
                  {y}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {categories.map((cat) => (
              <tr key={cat} className="border-t border-border">
                <td className="px-2 py-1 text-left">{cat}</td>
                {years.map((y) => {
                  const v = inst.category_breakdown[y]?.[cat] ?? 0;
                  return (
                    <td key={`${cat}-${y}`} className="px-2 py-1 text-right">
                      {v.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ReportList({ inst }: { inst: InstitutionDetail }) {
  function csv() {
    exportRowsAsCsv(
      inst.reports.map((r) => ({
        fiscal_year: r.fiscal_year,
        source: r.source,
        source_url: r.source_url,
        retrieved_at: r.retrieved_at,
        sha256_prefix: r.sha256_prefix,
        review_status: r.review_status,
        processing_review_status: r.processing_review_status,
        page_count: r.page_count,
        composite: r.composite_score,
        env: r.env,
        soc: r.soc,
        gov: r.gov,
      })),
      `${inst.slug}-reports.csv`,
    );
  }
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <div className="flex items-center justify-between gap-2">
        <h2 className="font-heading text-lg font-semibold">Reports</h2>
        <button
          type="button"
          onClick={csv}
          className="rounded-md border border-border bg-surface px-3 py-1 text-xs text-text-muted hover:text-text"
        >
          Export CSV
        </button>
      </div>
      {/* Report list: horizontal scroll with the FY column sticky so the
          user never loses which row they're on when swiping sideways. */}
      <div className="mt-3 -mx-4 overflow-x-auto px-4 sm:mx-0 sm:px-0">
      <table className="min-w-[640px] text-sm tabular [&_th:first-child]:sticky [&_th:first-child]:left-0 [&_th:first-child]:bg-surface [&_td:first-child]:sticky [&_td:first-child]:left-0 [&_td:first-child]:bg-surface">
        <thead>
          <tr className="text-xs uppercase tracking-wide text-text-muted">
            <th className="px-2 py-1 text-left">FY</th>
            <th className="px-2 py-1 text-left">Source</th>
            <th className="px-2 py-1 text-left">Retrieved</th>
            <th className="px-2 py-1 text-left">sha256</th>
            <th className="px-2 py-1 text-right">Pages</th>
            <th className="px-2 py-1 text-right">Composite</th>
            <th className="px-2 py-1 text-left">Review</th>
            <th className="px-2 py-1 text-right">PDF</th>
          </tr>
        </thead>
        <tbody>
          {inst.reports.map((r) => (
            <tr key={r.report_id} className="border-t border-border">
              <td className="px-2 py-1 text-left">{r.fiscal_year}</td>
              <td className="px-2 py-1 text-left">
                <a
                  href={r.source_url || "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="text-accent underline-offset-2 hover:underline"
                >
                  {r.source}
                </a>
              </td>
              <td className="px-2 py-1 text-left text-text-muted">
                {r.retrieved_at ? r.retrieved_at.slice(0, 10) : "—"}
              </td>
              <td className="px-2 py-1 text-left text-text-muted">
                <code className="text-[11px]">{r.sha256_prefix}</code>
              </td>
              <td className="px-2 py-1 text-right">{r.page_count}</td>
              <td className="px-2 py-1 text-right">{r.composite_score.toFixed(3)}</td>
              <td className="px-2 py-1 text-left">
                <span
                  className={[
                    "rounded-full px-1.5 py-0.5 text-[11px]",
                    r.processing_review_status === "auto_ok"
                      ? "border border-env/40 bg-env/10 text-env"
                      : "border border-warn/40 bg-warn/10 text-warn",
                  ].join(" ")}
                >
                  {r.processing_review_status}
                </span>
              </td>
              <td className="px-2 py-1 text-right">
                <a
                  href={pdfUrl(r.report_id, 1)}
                  target="_blank"
                  rel="noreferrer"
                  className="text-accent underline-offset-2 hover:underline"
                >
                  open
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}

function ExportPng({
  target,
  filename,
}: {
  target: { current: HTMLElement | null };
  filename: string;
}) {
  return (
    <button
      type="button"
      onClick={() => target.current && exportElementAsPng(target.current, filename)}
      className="rounded-md border border-border bg-surface px-2 py-1 text-xs text-text-muted hover:text-text"
    >
      Export PNG
    </button>
  );
}

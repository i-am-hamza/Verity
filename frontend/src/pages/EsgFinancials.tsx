import { type ReactNode, type RefObject, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { EmptyState, ErrorState, Loading } from "../components/StateViews";
import { exportElementAsPng, exportRowsAsCsv } from "../lib/export";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface EsgFinData {
  meta: {
    companies: number;
    company_years: number;
    financial_companies: number;
    years: [number, number];
    esg_scale: string;
    effect_unit: string;
  };
  variables: {
    dependent: string[];
    independent: string;
    controls: string[];
  };
  correlations: CorrelationRow[];
  regressions: RegressionRow[];
  robustness: RobustnessRow[];
  quartiles: QuartileRow[];
  trends: TrendRow[];
  points: PointRow[];
}

interface CorrelationRow {
  Group: string;
  ESG: string;
  Measure: string;
  rho: number;
  p: number;
  N: number;
}

interface RegressionRow {
  Group: string;
  Measure: string;
  Model: string;
  beta: number;
  se?: number;
  p: number;
  N: number;
}

interface RobustnessRow {
  Group: string;
  Measure: string;
  ESG_measure: string;
  beta_A2: number;
  p_A2: number;
  beta_B: number;
  p_B: number;
  N: number;
}

interface QuartileRow {
  Group: string;
  Quartile: string;
  N: number;
  ESG_median: number;
  "RoA (%)": number;
  "RoE (%)": number;
  "Net margin (%)": number;
  "Leverage (D/E)": number;
  "Market cap ($bn)": number;
}

interface TrendRow {
  Year: number;
  ESG: number;
  E: number;
  S: number;
  G: number;
  General: number;
  "RoA median (Financial)": number;
  "RoE median (Financial)": number;
  "RoA median (Non-financial)": number;
  "RoE median (Non-financial)": number;
}

interface PointRow {
  Company: string;
  Year: number;
  Financial: string;
  ESG: number;
  ROA: number | null;
  ROE: number | null;
  NetMargin: number | null;
  EPS: number | null;
  Leverage: number | null;
  lnMcap: number | null;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function loadEsgFinData(): Promise<EsgFinData> {
  const res = await fetch("/esg_financials_results.json");
  if (!res.ok) throw new Error(`Failed to load ESG data: ${res.status}`);
  return res.json() as Promise<EsgFinData>;
}

function pStar(p: number): string {
  if (p < 0.01) return "**";
  if (p < 0.05) return "*";
  return "";
}

function fmt(v: number | null | undefined, dp = 2): string {
  if (v === null || v === undefined) return "—";
  return v.toFixed(dp);
}

/** Extract short model code from full model string, e.g. "A2. Across…" → "A2" */
function modelCode(model: string): string {
  return model.split(".")[0] ?? model;
}

/** True for the two main models */
function isMain(model: string): boolean {
  const code = modelCode(model);
  return code === "A2" || code === "B";
}

// Ordered constants
const ESG_MEASURES = [
  "ESG composite",
  "Environmental",
  "Social",
  "Governance",
  "General",
] as const;

const FIN_MEASURES = [
  "RoA (%)",
  "RoE (%)",
  "Net margin (%)",
  "EPS",
  "Leverage (D/E)",
  "Market cap (log)",
] as const;

const SCATTER_OPTIONS: { key: keyof PointRow; label: string }[] = [
  { key: "ROE", label: "RoE (%)" },
  { key: "ROA", label: "RoA (%)" },
  { key: "NetMargin", label: "Net margin (%)" },
  { key: "EPS", label: "EPS" },
  { key: "Leverage", label: "Leverage (D/E)" },
  { key: "lnMcap", label: "Market cap (log)" },
];

const REG_MEASURES = ["RoA (%)", "RoE (%)", "Net margin (%)", "Market cap (log)"] as const;
const REG_MODELS_SHOW = ["A1", "A2", "B0", "B", "C"] as const;

const QUARTILE_ORDER = [
  "Q1 (lowest ESG)",
  "Q2",
  "Q3",
  "Q4 (highest ESG)",
] as const;

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function EsgFinancialsPage() {
  const q = useQuery({
    queryKey: ["esg-financials"],
    queryFn: loadEsgFinData,
    staleTime: Infinity,
  });

  if (q.isLoading) return <Loading label="Loading ESG & Financials…" />;
  if (q.isError)
    return (
      <ErrorState
        message="Could not load ESG & Financials data."
        detail={(q.error as Error).message}
      />
    );
  if (!q.data) return <EmptyState title="No ESG & Financials data yet." />;

  const d = q.data;

  return (
    <section className="flex flex-col gap-8">
      <header>
        <h1 className="font-heading text-2xl font-semibold tracking-tight">
          ESG &amp; Financials
        </h1>
        <p className="mt-1 text-sm text-text-muted">
          {d.meta.companies} companies · {d.meta.company_years} company-years ·
          FY{d.meta.years[0]}–{d.meta.years[1]} · ESG scale: {d.meta.esg_scale}
        </p>
      </header>

      {/* a. Summary */}
      <SummarySect />

      {/* b. Variables */}
      <VariablesSect variables={d.variables} />

      {/* c. Trends */}
      <TrendsSect trends={d.trends} />

      {/* d. Correlations */}
      <CorrelationsSect correlations={d.correlations} />

      {/* e. Scatter */}
      <ScatterSect points={d.points} />

      {/* f. Regression results */}
      <RegressionSect regressions={d.regressions} />

      {/* g. ESG quartiles */}
      <QuartilesSect quartiles={d.quartiles} />

      {/* h. Robustness + downloads */}
      <RobustnessSect robustness={d.robustness} />
    </section>
  );
}

// ---------------------------------------------------------------------------
// a. Summary
// ---------------------------------------------------------------------------

function SummarySect() {
  return (
    <section className="flex flex-col gap-4" aria-labelledby="summ-h">
      <h2 id="summ-h" className="font-heading text-lg font-semibold">
        Summary
      </h2>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatCard
          value="36 → 60"
          label="ESG composite (median)"
          detail="FY2020 to FY2025"
        />
        <StatCard
          value="ρ = 0.59"
          label="Bank RoE correlation"
          detail="Spearman, financial sector"
        />
        <StatCard
          value="≈ 0"
          label="Within-company effect"
          detail="Model B: year effects controlled"
        />
      </div>
      <div className="rounded-md border border-border bg-surface p-4 text-sm leading-relaxed text-text-muted">
        ESG disclosure is positively associated with profitability and firm value
        among GCC companies, most strongly among banks, where part of the
        association reflects country differences. Disclosure and profitability
        rose together over 2020–2025, but the evidence does not show that rising
        disclosure leads to higher financial performance.
      </div>
    </section>
  );
}

function StatCard({
  value,
  label,
  detail,
}: {
  value: string;
  label: string;
  detail: string;
}) {
  return (
    <div className="rounded-md border border-border bg-surface p-4">
      <div className="tabular text-2xl font-semibold tracking-tight text-accent">
        {value}
      </div>
      <div className="mt-1 text-sm font-medium text-text">{label}</div>
      <div className="mt-0.5 text-xs text-text-faint">{detail}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// b. Variables
// ---------------------------------------------------------------------------

const MODEL_EQUATIONS = [
  {
    code: "A1",
    eq: "Yᵢₜ = α + β·ESGᵢₜ + γ′Xᵢₜ + δₜ + ζⱼ + εᵢₜ",
    note: "Across companies; year + industry effects",
  },
  {
    code: "A2",
    eq: "Yᵢₜ = α + β·ESGᵢₜ + γ′Xᵢₜ + δₜ + ζⱼ + θᵏ + εᵢₜ",
    note: "A1 + country effects  [main across-company]",
    main: true,
  },
  {
    code: "B",
    eq: "Yᵢₜ = αᵢ + β·ESGᵢₜ + γ′Xᵢₜ + δₜ + εᵢₜ",
    note: "Within-company FE; year effects  [main within-company]",
    main: true,
  },
  {
    code: "C",
    eq: "Yᵢₜ = αᵢ + β·ESGᵢₜ₋₁ + γ′Xᵢₜ + δₜ + εᵢₜ",
    note: "ESG lagged one year — tests whether disclosure leads performance",
  },
];

function VariablesSect({
  variables,
}: {
  variables: EsgFinData["variables"];
}) {
  return (
    <section className="flex flex-col gap-4" aria-labelledby="vars-h">
      <h2 id="vars-h" className="font-heading text-lg font-semibold">
        Variables &amp; Models
      </h2>

      <div className="rounded-md border border-border bg-surface p-4 text-sm">
        <dl className="flex flex-col gap-3">
          <div>
            <dt className="font-medium text-text">Dependent</dt>
            <dd className="mt-0.5 text-text-muted">
              {variables.dependent.join("; ")}
            </dd>
          </div>
          <div>
            <dt className="font-medium text-text">Independent</dt>
            <dd className="mt-0.5 text-text-muted">{variables.independent}</dd>
          </div>
          <div>
            <dt className="font-medium text-text">Controls</dt>
            <dd className="mt-0.5 text-text-muted">
              {variables.controls.join("; ")}
            </dd>
          </div>
        </dl>
      </div>

      <div className="overflow-x-auto rounded-md border border-border bg-surface">
        <table className="w-full min-w-[560px] text-sm" aria-label="Model equations">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
              <th className="py-2 pl-4 pr-3 text-left" scope="col">
                Model
              </th>
              <th className="py-2 px-3 text-left font-mono" scope="col">
                Equation
              </th>
              <th className="py-2 pl-3 pr-4 text-left" scope="col">
                Note
              </th>
            </tr>
          </thead>
          <tbody>
            {MODEL_EQUATIONS.map((m) => (
              <tr
                key={m.code}
                className={[
                  "border-b border-border last:border-0",
                  m.main ? "bg-accent/5" : "",
                ].join(" ")}
              >
                <td className="py-2 pl-4 pr-3 font-mono font-semibold text-accent">
                  {m.code}
                  {m.main && (
                    <span className="ml-1.5 rounded bg-accent/15 px-1 py-0.5 text-[10px]">
                      main
                    </span>
                  )}
                </td>
                <td className="py-2 px-3 font-mono text-text">{m.eq}</td>
                <td className="py-2 pl-3 pr-4 text-text-muted">{m.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-text-faint">
        β entered per +10 ESG points. Standard errors clustered by company. α
        <sub>i</sub> = company fixed effect; δ<sub>t</sub> = year effect; ζ
        <sub>j</sub> = industry effect; θ<sub>k</sub> = country effect.
      </p>
    </section>
  );
}

// ---------------------------------------------------------------------------
// c. Trends
// ---------------------------------------------------------------------------

function TrendsSect({ trends }: { trends: TrendRow[] }) {
  const esgRef = useRef<HTMLDivElement>(null);
  const finRef = useRef<HTMLDivElement>(null);

  const esgCsvRows = trends.map((t) => ({
    Year: t.Year,
    ESG: t.ESG,
    Environmental: t.E,
    Social: t.S,
    Governance: t.G,
    General: t.General,
  }));

  const finCsvRows = trends.map((t) => ({
    Year: t.Year,
    "RoA (Financial)": t["RoA median (Financial)"],
    "RoE (Financial)": t["RoE median (Financial)"],
    "RoA (Non-financial)": t["RoA median (Non-financial)"],
    "RoE (Non-financial)": t["RoE median (Non-financial)"],
  }));

  return (
    <section className="flex flex-col gap-4" aria-labelledby="trends-h">
      <h2 id="trends-h" className="font-heading text-lg font-semibold">
        Trends
      </h2>

      {/* ESG trends */}
      <ChartCard
        title="ESG composite &amp; pillars by year"
        description="Median score across all 65 companies per year (0-100 scale)."
        chartRef={esgRef}
        onExportPng={() =>
          esgRef.current && exportElementAsPng(esgRef.current, "esg_trends.png")
        }
        onExportCsv={() => exportRowsAsCsv(esgCsvRows, "esg_trends.csv")}
      >
        <div ref={esgRef} className="h-64 w-full sm:h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={trends}
              margin={{ top: 4, right: 8, bottom: 4, left: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border))" />
              <XAxis
                dataKey="Year"
                tick={{ fontSize: 12, fill: "rgb(var(--text-muted))" }}
              />
              <YAxis
                domain={[20, 75]}
                tick={{ fontSize: 12, fill: "rgb(var(--text-muted))" }}
                label={{
                  value: "Score (0-100)",
                  angle: -90,
                  position: "insideLeft",
                  offset: 12,
                  style: { fontSize: 11, fill: "rgb(var(--text-faint))" },
                }}
              />
              <Tooltip
                contentStyle={{
                  background: "rgb(var(--surface))",
                  border: "1px solid rgb(var(--border))",
                  borderRadius: "6px",
                  fontSize: 12,
                  color: "rgb(var(--text))",
                }}
              />
              <Legend
                wrapperStyle={{ fontSize: 12, color: "rgb(var(--text-muted))" }}
              />
              <Line type="monotone" dataKey="ESG" name="Composite" stroke="rgb(var(--accent))" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="E" name="Environmental" stroke="rgb(var(--env))" strokeWidth={2} dot={false} strokeDasharray="4 2" />
              <Line type="monotone" dataKey="S" name="Social" stroke="rgb(var(--soc))" strokeWidth={2} dot={false} strokeDasharray="4 2" />
              <Line type="monotone" dataKey="G" name="Governance" stroke="rgb(var(--gov))" strokeWidth={2} dot={false} strokeDasharray="4 2" />
              <Line type="monotone" dataKey="General" name="General" stroke="rgb(var(--text-muted))" strokeWidth={1.5} dot={false} strokeDasharray="2 3" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </ChartCard>

      {/* Financial trends */}
      <ChartCard
        title="Median RoA &amp; RoE by year: financial vs non-financial"
        description="Median return on assets and equity, split by sector."
        chartRef={finRef}
        onExportPng={() =>
          finRef.current && exportElementAsPng(finRef.current, "financial_trends.png")
        }
        onExportCsv={() => exportRowsAsCsv(finCsvRows, "financial_trends.csv")}
      >
        <div ref={finRef} className="h-64 w-full sm:h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={trends}
              margin={{ top: 4, right: 8, bottom: 4, left: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border))" />
              <XAxis dataKey="Year" tick={{ fontSize: 12, fill: "rgb(var(--text-muted))" }} />
              <YAxis tick={{ fontSize: 12, fill: "rgb(var(--text-muted))" }}
                label={{ value: "% return", angle: -90, position: "insideLeft", offset: 12, style: { fontSize: 11, fill: "rgb(var(--text-faint))" } }}
              />
              <Tooltip
                contentStyle={{ background: "rgb(var(--surface))", border: "1px solid rgb(var(--border))", borderRadius: "6px", fontSize: 12, color: "rgb(var(--text))" }}
              />
              <Legend wrapperStyle={{ fontSize: 12, color: "rgb(var(--text-muted))" }} />
              <Line type="monotone" dataKey="RoA median (Financial)" name="RoA · Financial" stroke="rgb(var(--accent))" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="RoE median (Financial)" name="RoE · Financial" stroke="rgb(var(--accent))" strokeWidth={2} dot={false} strokeDasharray="5 3" />
              <Line type="monotone" dataKey="RoA median (Non-financial)" name="RoA · Non-fin" stroke="rgb(var(--env))" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="RoE median (Non-financial)" name="RoE · Non-fin" stroke="rgb(var(--env))" strokeWidth={2} dot={false} strokeDasharray="5 3" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </ChartCard>
    </section>
  );
}

// ---------------------------------------------------------------------------
// d. Correlations heatmap
// ---------------------------------------------------------------------------

type CorrGroup = "All companies" | "Financial" | "Non-financial";
const CORR_GROUPS: CorrGroup[] = ["All companies", "Financial", "Non-financial"];

function CorrelationsSect({ correlations }: { correlations: CorrelationRow[] }) {
  const [group, setGroup] = useState<CorrGroup>("All companies");
  const tableRef = useRef<HTMLDivElement>(null);

  const filtered = correlations.filter((r) => r.Group === group);

  const lookup = new Map<string, CorrelationRow>();
  for (const r of filtered) lookup.set(`${r.ESG}||${r.Measure}`, r);

  const csvRows = [...ESG_MEASURES].flatMap((esg) =>
    [...FIN_MEASURES].map((fin) => {
      const r = lookup.get(`${esg}||${fin}`);
      return { Group: group, ESG: esg, Measure: fin, rho: r?.rho ?? null, p: r?.p ?? null, N: r?.N ?? null };
    })
  );

  return (
    <section className="flex flex-col gap-4" aria-labelledby="corr-h">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="corr-h" className="font-heading text-lg font-semibold">
            Correlations
          </h2>
          <p className="mt-0.5 text-xs text-text-muted">
            Spearman ρ. * p&lt;0.05, ** p&lt;0.01. Hover cells for detail.
          </p>
        </div>
        <GroupToggle<CorrGroup>
          value={group}
          options={CORR_GROUPS}
          onChange={setGroup}
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => tableRef.current && exportElementAsPng(tableRef.current, "correlations_heatmap.png")}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export PNG
        </button>
        <button
          type="button"
          onClick={() => exportRowsAsCsv(csvRows, "correlations.csv")}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export CSV
        </button>
      </div>

      <div ref={tableRef} className="overflow-x-auto rounded-md border border-border bg-surface">
        <table className="w-full min-w-[600px] border-collapse text-xs" aria-label="Correlation heatmap">
          <thead>
            <tr>
              <th className="border-b border-r border-border p-2 text-left text-xs font-medium text-text-muted" scope="col">
                ESG ↓ / Financial →
              </th>
              {FIN_MEASURES.map((m) => (
                <th key={m} scope="col" className="border-b border-r border-border p-2 text-center text-xs font-medium text-text-muted last:border-r-0">
                  {m}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ESG_MEASURES.map((esg) => (
              <tr key={esg} className="border-b border-border last:border-0">
                <th scope="row" className="border-r border-border p-2 text-left text-xs font-medium text-text">
                  {esg}
                </th>
                {FIN_MEASURES.map((fin) => {
                  const r = lookup.get(`${esg}||${fin}`);
                  if (!r) return <td key={fin} className="border-r border-border p-2 last:border-r-0" />;
                  const abs = Math.min(Math.abs(r.rho), 1);
                  const opacity = Math.round(abs * 65);
                  const bgStyle =
                    r.rho >= 0
                      ? { backgroundColor: `rgb(var(--accent) / ${opacity}%)` }
                      : { backgroundColor: `rgb(var(--warn) / ${opacity}%)` };
                  return (
                    <td
                      key={fin}
                      className="border-r border-border p-2 text-center tabular last:border-r-0"
                      style={bgStyle}
                      title={`ρ = ${r.rho.toFixed(3)}, p = ${r.p < 0.001 ? "<0.001" : r.p.toFixed(3)}, N = ${r.N}`}
                      aria-label={`${esg} vs ${fin}: ρ=${r.rho.toFixed(3)} ${pStar(r.p) || "n.s."}`}
                    >
                      <span className="font-semibold text-text">
                        {r.rho.toFixed(2)}
                      </span>
                      <sup className="text-text">{pStar(r.p)}</sup>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-text-faint">
        Blue = positive, orange = negative. Intensity ∝ |ρ|.
      </p>
    </section>
  );
}

// ---------------------------------------------------------------------------
// e. Scatter
// ---------------------------------------------------------------------------

function ScatterSect({ points }: { points: PointRow[] }) {
  const [measure, setMeasure] = useState<keyof PointRow>("ROE");
  const chartRef = useRef<HTMLDivElement>(null);

  const label =
    SCATTER_OPTIONS.find((o) => o.key === measure)?.label ?? String(measure);

  const finPoints = points
    .filter((p) => p.Financial === "Yes" && p[measure] !== null && p.ESG !== null)
    .map((p) => ({ x: p.ESG, y: p[measure] as number, name: `${p.Company} ${p.Year}` }));

  const nonFinPoints = points
    .filter((p) => p.Financial === "No" && p[measure] !== null && p.ESG !== null)
    .map((p) => ({ x: p.ESG, y: p[measure] as number, name: `${p.Company} ${p.Year}` }));

  const csvRows = points
    .filter((p) => p[measure] !== null)
    .map((p) => ({
      Company: p.Company,
      Year: p.Year,
      Financial: p.Financial,
      ESG: p.ESG,
      [label]: p[measure],
    }));

  return (
    <section className="flex flex-col gap-4" aria-labelledby="scatter-h">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="scatter-h" className="font-heading text-lg font-semibold">
            Scatter: ESG composite vs financial measure
          </h2>
          <p className="mt-0.5 text-xs text-text-muted">
            Each point = one company-year. Hover for company name and year.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {SCATTER_OPTIONS.map((o) => (
            <button
              key={o.key}
              type="button"
              onClick={() => setMeasure(o.key)}
              className={[
                "rounded-md border px-3 py-1.5 text-xs",
                measure === o.key
                  ? "border-accent bg-accent/10 text-accent"
                  : "border-border bg-surface text-text-muted hover:text-text",
              ].join(" ")}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => chartRef.current && exportElementAsPng(chartRef.current, `scatter_esg_vs_${String(measure).toLowerCase()}.png`)}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export PNG
        </button>
        <button
          type="button"
          onClick={() => exportRowsAsCsv(csvRows, `scatter_esg_vs_${String(measure).toLowerCase()}.csv`)}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export CSV
        </button>
      </div>

      <div
        ref={chartRef}
        className="rounded-md border border-border bg-surface p-2"
      >
        <div className="h-72 w-full sm:h-96">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 8, right: 16, bottom: 20, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border))" />
              <XAxis
                dataKey="x"
                name="ESG composite"
                type="number"
                domain={[0, 100]}
                tick={{ fontSize: 11, fill: "rgb(var(--text-muted))" }}
                label={{ value: "ESG composite (0-100)", position: "insideBottom", offset: -10, style: { fontSize: 11, fill: "rgb(var(--text-faint))" } }}
              />
              <YAxis
                dataKey="y"
                name={label}
                type="number"
                tick={{ fontSize: 11, fill: "rgb(var(--text-muted))" }}
                label={{ value: label, angle: -90, position: "insideLeft", offset: 12, style: { fontSize: 11, fill: "rgb(var(--text-faint))" } }}
              />
              <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                content={({ payload }) => {
                  if (!payload?.length) return null;
                  const pt = payload[0]?.payload as { x: number; y: number; name: string } | undefined;
                  if (!pt) return null;
                  return (
                    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-pop">
                      <div className="font-medium text-text">{pt.name}</div>
                      <div className="mt-1 text-text-muted">
                        ESG: <span className="tabular text-text">{pt.x.toFixed(1)}</span>
                      </div>
                      <div className="text-text-muted">
                        {label}: <span className="tabular text-text">{fmt(pt.y)}</span>
                      </div>
                    </div>
                  );
                }}
              />
              <Legend wrapperStyle={{ fontSize: 12, color: "rgb(var(--text-muted))" }} />
              <Scatter
                name="Financial"
                data={finPoints}
                fill="rgb(var(--accent))"
                fillOpacity={0.7}
                r={3}
              />
              <Scatter
                name="Non-financial"
                data={nonFinPoints}
                fill="rgb(var(--env))"
                fillOpacity={0.5}
                r={3}
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// f. Regression results
// ---------------------------------------------------------------------------

type RegGroup = "All companies" | "Financial" | "Non-financial";
const REG_GROUPS: RegGroup[] = ["All companies", "Financial", "Non-financial"];

function RegressionSect({ regressions }: { regressions: RegressionRow[] }) {
  const [group, setGroup] = useState<RegGroup>("All companies");
  const [measure, setMeasure] = useState<string>(REG_MEASURES[0]);

  const filtered = regressions.filter(
    (r) => r.Group === group && r.Measure === measure
  );

  const byModel = new Map<string, RegressionRow>();
  for (const r of filtered) byModel.set(modelCode(r.Model), r);

  const csvRows = REG_MODELS_SHOW.map((code) => {
    const r = byModel.get(code);
    return {
      Group: group,
      Measure: measure,
      Model: code,
      β: r?.beta ?? null,
      p: r?.p ?? null,
      N: r?.N ?? null,
      main: isMain(code + ".") ? "yes" : "no",
    };
  });

  return (
    <section className="flex flex-col gap-4" aria-labelledby="reg-h">
      <div>
        <h2 id="reg-h" className="font-heading text-lg font-semibold">
          Regression results
        </h2>
        <p className="mt-0.5 text-xs text-text-muted">
          Effect per +10 ESG points (β). Standard errors clustered by company.
          * p&lt;0.05, ** p&lt;0.01. Shaded rows = main models.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <GroupToggle<RegGroup> value={group} options={REG_GROUPS} onChange={setGroup} />
        <div className="flex flex-wrap gap-1">
          {REG_MEASURES.map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMeasure(m)}
              className={[
                "rounded-md border px-3 py-1.5 text-xs",
                measure === m
                  ? "border-accent bg-accent/10 text-accent"
                  : "border-border bg-surface text-text-muted hover:text-text",
              ].join(" ")}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => exportRowsAsCsv(csvRows, `regression_${group.replace(/ /g,"_")}_${measure.replace(/[^a-z0-9]/gi,"_")}.csv`)}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export CSV
        </button>
      </div>

      <div className="overflow-x-auto rounded-md border border-border bg-surface">
        <table className="w-full min-w-[480px] text-sm tabular" aria-label="Regression results table">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
              <th className="py-2 pl-4 pr-3 text-left" scope="col">Model</th>
              <th className="py-2 px-3 text-right" scope="col">β</th>
              <th className="py-2 px-3 text-right" scope="col">p</th>
              <th className="py-2 pl-3 pr-4 text-right" scope="col">N</th>
            </tr>
          </thead>
          <tbody>
            {REG_MODELS_SHOW.map((code) => {
              const r = byModel.get(code);
              const fullModel = r?.Model ?? code;
              const main = isMain(fullModel);
              return (
                <tr
                  key={code}
                  className={[
                    "border-b border-border last:border-0",
                    main ? "bg-accent/5" : "",
                  ].join(" ")}
                >
                  <td className="py-2 pl-4 pr-3 font-mono">
                    <span className="font-semibold text-accent">{code}</span>
                    {main && (
                      <span className="ml-1.5 rounded bg-accent/15 px-1 py-0.5 text-[10px]">
                        main
                      </span>
                    )}
                    <span className="ml-2 text-xs text-text-faint">
                      {fullModel.split(". ")[1]?.split("[")[0]?.trim() ?? ""}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right font-mono text-text">
                    {r ? (
                      <>
                        {fmt(r.beta, 3)}
                        <sup>{pStar(r.p)}</sup>
                      </>
                    ) : "—"}
                  </td>
                  <td className="py-2 px-3 text-right font-mono text-text-muted">
                    {r ? (r.p < 0.001 ? "<0.001" : fmt(r.p, 3)) : "—"}
                  </td>
                  <td className="py-2 pl-3 pr-4 text-right text-text-muted">
                    {r?.N ?? "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// g. ESG quartiles
// ---------------------------------------------------------------------------

type QGroup = "Financial" | "Non-financial";
const Q_GROUPS: QGroup[] = ["Financial", "Non-financial"];
const Q_MEASURES = ["RoA (%)", "RoE (%)", "Market cap ($bn)"] as const;

function QuartilesSect({ quartiles }: { quartiles: QuartileRow[] }) {
  const [group, setGroup] = useState<QGroup>("Financial");
  const [measure, setMeasure] = useState<typeof Q_MEASURES[number]>("RoE (%)");
  const chartRef = useRef<HTMLDivElement>(null);

  const rows = quartiles
    .filter((r) => r.Group === group)
    .sort((a, b) => QUARTILE_ORDER.indexOf(a.Quartile as (typeof QUARTILE_ORDER)[number]) - QUARTILE_ORDER.indexOf(b.Quartile as (typeof QUARTILE_ORDER)[number]));

  const chartData = rows.map((r) => ({
    Quartile: r.Quartile.replace(" (lowest ESG)", " ↓").replace(" (highest ESG)", " ↑"),
    [measure]: r[measure],
    N: r.N,
  }));

  const csvRows = rows.map((r) => ({
    Group: r.Group,
    Quartile: r.Quartile,
    N: r.N,
    ESG_median: r.ESG_median,
    [measure]: r[measure],
  }));

  return (
    <section className="flex flex-col gap-4" aria-labelledby="quartile-h">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="quartile-h" className="font-heading text-lg font-semibold">
            ESG quartiles
          </h2>
          <p className="mt-0.5 text-xs text-text-muted">
            Median financial performance by ESG disclosure quartile.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <GroupToggle<QGroup> value={group} options={Q_GROUPS} onChange={setGroup} />
          <div className="flex flex-wrap gap-1">
            {Q_MEASURES.map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMeasure(m)}
                className={[
                  "rounded-md border px-3 py-1.5 text-xs",
                  measure === m
                    ? "border-accent bg-accent/10 text-accent"
                    : "border-border bg-surface text-text-muted hover:text-text",
                ].join(" ")}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => chartRef.current && exportElementAsPng(chartRef.current, `quartiles_${group.replace(/ /g,"_")}_${measure.replace(/[^a-z0-9]/gi,"_")}.png`)}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export PNG
        </button>
        <button
          type="button"
          onClick={() => exportRowsAsCsv(csvRows, `quartiles_${group.replace(/ /g,"_")}.csv`)}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export CSV
        </button>
      </div>

      <div
        ref={chartRef}
        className="rounded-md border border-border bg-surface p-2"
      >
        <div className="h-64 w-full sm:h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{ top: 8, right: 8, bottom: 4, left: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border))" vertical={false} />
              <XAxis
                dataKey="Quartile"
                tick={{ fontSize: 11, fill: "rgb(var(--text-muted))" }}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "rgb(var(--text-muted))" }}
                label={{ value: measure, angle: -90, position: "insideLeft", offset: 12, style: { fontSize: 11, fill: "rgb(var(--text-faint))" } }}
              />
              <Tooltip
                contentStyle={{ background: "rgb(var(--surface))", border: "1px solid rgb(var(--border))", borderRadius: "6px", fontSize: 12, color: "rgb(var(--text))" }}
                formatter={(value: number, _name: string, props: { payload?: { N?: number } }) => [
                  `${fmt(value)} (N=${props.payload?.N ?? "?"})`,
                  measure,
                ]}
              />
              <Bar dataKey={measure} fill="rgb(var(--accent))" fillOpacity={0.85} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// h. Robustness + downloads
// ---------------------------------------------------------------------------

function RobustnessSect({ robustness }: { robustness: RobustnessRow[] }) {
  const csvRows = robustness.map((r) => ({
    Group: r.Group,
    Measure: r.Measure,
    ESG_measure: r.ESG_measure,
    beta_A2: r.beta_A2,
    p_A2: r.p_A2,
    beta_B: r.beta_B,
    p_B: r.p_B,
    N: r.N,
  }));

  return (
    <section className="flex flex-col gap-4" aria-labelledby="robust-h">
      <h2 id="robust-h" className="font-heading text-lg font-semibold">
        Robustness &amp; limitations
      </h2>

      <div className="rounded-md border border-border bg-surface p-4 text-sm leading-relaxed text-text-muted">
        <p>
          Results hold across E, S, G and General sub-scores as the independent
          variable and across the six outcome measures (Table: ESG sub-scores on
          financial measures, A2 and B columns). The cross-sectional correlations
          (models A1 and A2) partly reflect persistent country differences —
          Saudi and UAE companies both score higher on ESG and operate in
          higher-margin sectors — rather than a causal effect of disclosure.
          Within-company estimates (model B) remove this confound and are
          uniformly small and non-significant.
        </p>
        <p className="mt-2">
          Limitations: six years of panel data limit statistical power for the
          within-company models. Financial variables for Sipchem FY2025 show a
          net loss; outlier sensitivity checks excluding observations with
          |RoE|&gt;100% do not change conclusions. Market cap is proxied by
          ln(market cap in USD at year-end), which ties ESG to size — a known
          confounder in cross-sectional ESG research.
        </p>
      </div>

      {/* Robustness table */}
      <div className="overflow-x-auto rounded-md border border-border bg-surface">
        <table className="w-full min-w-[600px] text-xs tabular" aria-label="Robustness checks">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
              <th className="py-2 pl-4 pr-3 text-left" scope="col">Group</th>
              <th className="py-2 px-3 text-left" scope="col">Measure</th>
              <th className="py-2 px-3 text-left" scope="col">ESG measure</th>
              <th className="py-2 px-3 text-right" scope="col">β A2</th>
              <th className="py-2 px-3 text-right" scope="col">p A2</th>
              <th className="py-2 px-3 text-right" scope="col">β B</th>
              <th className="py-2 pl-3 pr-4 text-right" scope="col">p B</th>
            </tr>
          </thead>
          <tbody>
            {robustness.map((r, i) => (
              <tr key={i} className="border-b border-border last:border-0">
                <td className="py-1.5 pl-4 pr-3 text-text-muted">{r.Group}</td>
                <td className="py-1.5 px-3 text-text-muted">{r.Measure}</td>
                <td className="py-1.5 px-3 text-text">{r.ESG_measure}</td>
                <td className="py-1.5 px-3 text-right font-mono text-text">
                  {fmt(r.beta_A2, 3)}<sup>{pStar(r.p_A2)}</sup>
                </td>
                <td className="py-1.5 px-3 text-right font-mono text-text-muted">
                  {r.p_A2 < 0.001 ? "<0.001" : fmt(r.p_A2, 3)}
                </td>
                <td className="py-1.5 px-3 text-right font-mono text-text">
                  {fmt(r.beta_B, 3)}<sup>{pStar(r.p_B)}</sup>
                </td>
                <td className="py-1.5 pl-3 pr-4 text-right font-mono text-text-muted">
                  {r.p_B < 0.001 ? "<0.001" : fmt(r.p_B, 3)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Downloads */}
      <div className="flex flex-wrap gap-2">
        <a
          href="/esg_financials_results.json"
          download
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Download JSON
        </a>
        <a
          href="/downloads/ESG_vs_Financials_Analysis_FINAL.xlsx"
          download
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Download Excel
        </a>
        <button
          type="button"
          onClick={() => exportRowsAsCsv(csvRows, "robustness_checks.csv")}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export table CSV
        </button>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Shared sub-components
// ---------------------------------------------------------------------------

function ChartCard({
  title,
  description,
  chartRef,
  onExportPng,
  onExportCsv,
  children,
}: {
  title: string;
  description: string;
  chartRef: RefObject<HTMLDivElement | null>;
  onExportPng: () => void;
  onExportCsv: () => void;
  children: ReactNode;
}) {
  return (
    <div className="rounded-md border border-border bg-surface p-4" ref={chartRef}>
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3
            className="font-heading text-sm font-semibold text-text"
            dangerouslySetInnerHTML={{ __html: title }}
          />
          <p className="mt-0.5 text-xs text-text-muted">{description}</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={onExportPng}
            className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
          >
            Export PNG
          </button>
          <button
            type="button"
            onClick={onExportCsv}
            className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
          >
            Export CSV
          </button>
        </div>
      </div>
      {children}
    </div>
  );
}

function GroupToggle<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: T[];
  onChange: (v: T) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1" role="group">
      {options.map((o) => (
        <button
          key={o}
          type="button"
          onClick={() => onChange(o)}
          className={[
            "rounded-md border px-3 py-1.5 text-xs",
            value === o
              ? "border-accent bg-accent/10 text-accent"
              : "border-border bg-surface text-text-muted hover:text-text",
          ].join(" ")}
        >
          {o}
        </button>
      ))}
    </div>
  );
}

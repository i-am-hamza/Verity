import {
  type ReactNode,
  type RefObject,
  useMemo,
  useRef,
  useState,
} from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { EmptyState, ErrorState, Loading } from "../components/StateViews";
import { exportElementAsPng, exportRowsAsCsv } from "../lib/export";
import { exportCsvUrl, exportXlsxUrl } from "../lib/api/client";

// ---------------------------------------------------------------------------
// Types — mirror analysis/results/esg_financials_results.json one-to-one
// ---------------------------------------------------------------------------

interface DescriptiveRow {
  Group: string;
  Variable: string;
  N: number;
  Mean: number;
  SD: number;
  Min: number;
  P25: number;
  Median: number;
  P75: number;
  Max: number;
}

interface CorrelationMatrixRow {
  Variable: string;
  [column: string]: number | string;
}

interface VifRow {
  Group: string;
  Variable: string;
  VIF: number;
}

interface SpearmanRow {
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
  se: number;
  p: number;
  N: number;
  R2: number | null;
  first_stage_F: number | null;
}

interface HausmanRow {
  Group: string;
  Measure: string;
  chi2: number;
  df: number;
  p: number;
  Preferred: string;
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
  "Q median (Financial)": number;
  "RoA median (Non-financial)": number;
  "RoE median (Non-financial)": number;
  "Q median (Non-financial)": number;
}

interface BoardRow {
  Group: string;
  Test: string;
  beta: number;
  p: number;
  N: number;
}

interface EsgFinData {
  meta: {
    companies: number;
    company_years: number;
    financial_companies: number;
    effect_unit: string;
  };
  descriptives: DescriptiveRow[];
  correlation_matrix: CorrelationMatrixRow[];
  vif: VifRow[];
  spearman: SpearmanRow[];
  regressions: RegressionRow[];
  hausman: HausmanRow[];
  board_size: BoardRow[];
  trends: TrendRow[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function loadData(): Promise<EsgFinData> {
  const res = await fetch("/esg_financials_results.json");
  if (!res.ok) throw new Error(`Failed to load data: ${res.status}`);
  return res.json() as Promise<EsgFinData>;
}

function pStar(p: number | null | undefined): string {
  if (p === null || p === undefined) return "";
  if (p < 0.001) return "***";
  if (p < 0.01) return "**";
  if (p < 0.05) return "*";
  return "";
}

function fmt(v: number | null | undefined, dp = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toFixed(dp);
}

function fmtP(p: number | null | undefined): string {
  if (p === null || p === undefined || Number.isNaN(p)) return "—";
  return p < 0.001 ? "<0.001" : p.toFixed(3);
}

function modelCode(model: string): string {
  return model.split(".")[0]?.trim() ?? model;
}

const FIN_MEASURES = [
  "RoA (%)",
  "RoE (%)",
  "Net margin (%)",
  "EPS",
  "Tobin's Q",
  "Price-to-book",
] as const;
type FinMeasure = (typeof FIN_MEASURES)[number];

const GROUPS = ["All companies", "Financial", "Non-financial"] as const;
type Group = (typeof GROUPS)[number];

const REG_MODELS: { code: string; label: string; main?: boolean }[] = [
  { code: "A1", label: "A1" },
  { code: "A2", label: "A2", main: true },
  { code: "RE", label: "RE" },
  { code: "B0", label: "B0" },
  { code: "B", label: "B", main: true },
  { code: "C", label: "C" },
  { code: "D", label: "D" },
  { code: "IV", label: "IV" },
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function EsgFinancialsPage() {
  const q = useQuery({
    queryKey: ["esg-financials-v2"],
    queryFn: loadData,
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
    <section className="flex flex-col gap-10">
      <header>
        <h1 className="font-heading text-2xl font-semibold tracking-tight">
          ESG &amp; Financials
        </h1>
        <p className="mt-1 text-sm text-text-muted">
          {d.meta.companies} companies · {d.meta.company_years} company-years ·{" "}
          FY2020–FY2025 · {d.meta.financial_companies} financial companies ·
          effects reported per +10 ESG points
        </p>
      </header>

      <SummarySect />
      <VariablesSect />
      <ModelsSect />
      <TrendsSect trends={d.trends} />
      <DescriptivesSect rows={d.descriptives} />
      <CorrelationsSect
        spearman={d.spearman}
        matrix={d.correlation_matrix}
        vif={d.vif}
      />
      <HausmanSect rows={d.hausman} />
      <RegressionsSect rows={d.regressions} />
      <BoardSizeSect rows={d.board_size} />
      <ComparisonSect />
      <DownloadsSect />
    </section>
  );
}

// ---------------------------------------------------------------------------
// a. Summary
// ---------------------------------------------------------------------------

function SummarySect() {
  return (
    <section className="flex flex-col gap-3" aria-labelledby="summ-h">
      <h2 id="summ-h" className="font-heading text-lg font-semibold">
        Summary
      </h2>
      <div className="rounded-md border border-border bg-surface p-4 text-sm leading-relaxed text-text">
        Companies that disclose more about ESG tend to be more profitable and
        more highly valued, especially banks, partly reflecting country
        differences. Disclosure and profitability rose together over 2020–2025,
        but faster disclosure growth did not bring faster improvement in
        profitability or value: an association, not cause and effect.
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// b. Variables
// ---------------------------------------------------------------------------

function VariablesSect() {
  return (
    <section className="flex flex-col gap-3" aria-labelledby="vars-h">
      <h2 id="vars-h" className="font-heading text-lg font-semibold">
        Variables
      </h2>
      <div className="rounded-md border border-border bg-surface p-4 text-sm">
        <dl className="flex flex-col gap-3">
          <div>
            <dt className="font-medium text-text">Dependent</dt>
            <dd className="mt-0.5 text-text-muted">
              RoA, RoE, net margin, EPS, Tobin&apos;s Q, price-to-book
            </dd>
          </div>
          <div>
            <dt className="font-medium text-text">Independent</dt>
            <dd className="mt-0.5 text-text-muted">
              ESG composite (0–100). E, S, G and General pillars are used in
              robustness.
            </dd>
          </div>
          <div>
            <dt className="font-medium text-text">Controls</dt>
            <dd className="mt-0.5 text-text-muted">
              ln(total assets), leverage (debt/equity), board size, ln(1 + firm
              age). Models add year, industry, country or company effects
              depending on the design.
            </dd>
          </div>
        </dl>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// c. How the models work
// ---------------------------------------------------------------------------

type ModelCard = {
  code: string;
  title: string;
  question: string;
  analogy: string;
  main?: boolean;
};

const MODEL_CARDS: ModelCard[] = [
  {
    code: "A1 / A2",
    title: "Across companies",
    question:
      "Among all 390 company-years, do higher ESG disclosers tend to have higher financial results?",
    analogy:
      "A1 compares students in the same class and year group. A2 also compares students from the same school: it holds country constant so the effect is a within-country comparison.",
    main: true,
  },
  {
    code: "RE",
    title: "Random effects",
    question:
      "Blend across- and within-company variation under the assumption that company differences are random noise rather than fixed traits.",
    analogy:
      "A middle ground between asking \"which students study more?\" and \"when does a student study more?\". It is efficient when the Hausman test does not reject it.",
  },
  {
    code: "B0 / B",
    title: "Within a company",
    question:
      "When the same company's ESG disclosure goes up over time, do its own results go up?",
    analogy:
      "Follow one student year by year. B0 uses only that student's time pattern; B also removes shocks shared with other students that year (e.g. an easier exam).",
    main: true,
  },
  {
    code: "C",
    title: "ESG first",
    question:
      "Does an increase in ESG this year predict a higher financial result next year?",
    analogy:
      "Hours studied in September measured against the November grade — gives disclosure time to feed through.",
  },
  {
    code: "D",
    title: "Reverse: results first",
    question:
      "Does a higher financial result this year predict higher ESG disclosure next year?",
    analogy:
      "The reverse arrow — do good grades push a student to study more next semester? Guards against reading the association in only one direction.",
  },
  {
    code: "IV",
    title: "2SLS (instrument)",
    question:
      "What is the effect of ESG that is purely driven by sector-wide disclosure habits, not by the company's own choices?",
    analogy:
      "Use the average study hours of peers in other classes as a stand-in for how much \"culture\" alone pushes a student to study. Only works when that peer culture clearly moves the student's hours (strong first-stage F). Our first-stage F is below 10 for every measure, so the IV estimates are weak and reported for completeness.",
  },
];

function ModelsSect() {
  return (
    <section className="flex flex-col gap-3" aria-labelledby="models-h">
      <h2 id="models-h" className="font-heading text-lg font-semibold">
        How the models work
      </h2>
      <p className="text-sm text-text-muted">
        Analogy: ESG disclosure is like hours studied, the financial result is
        the exam grade. Each model asks a different question.
      </p>
      <div className="overflow-x-auto rounded-md border border-border bg-surface">
        <table
          className="w-full min-w-[640px] text-sm"
          aria-label="How each model works"
        >
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
              <th className="py-2 pl-4 pr-3 text-left" scope="col">
                Model
              </th>
              <th className="py-2 px-3 text-left" scope="col">
                What it asks
              </th>
              <th className="py-2 pl-3 pr-4 text-left" scope="col">
                Analogy
              </th>
            </tr>
          </thead>
          <tbody>
            {MODEL_CARDS.map((m) => (
              <tr
                key={m.code}
                className={[
                  "border-b border-border align-top last:border-0",
                  m.main ? "bg-accent/5" : "",
                ].join(" ")}
              >
                <td className="py-2 pl-4 pr-3 font-mono text-sm font-semibold text-accent">
                  {m.code}
                  <div className="text-[11px] font-normal text-text-muted">
                    {m.title}
                  </div>
                  {m.main && (
                    <div className="mt-1 inline-block rounded bg-accent/15 px-1 py-0.5 text-[10px]">
                      main
                    </div>
                  )}
                </td>
                <td className="py-2 px-3 text-text">{m.question}</td>
                <td className="py-2 pl-3 pr-4 text-text-muted">{m.analogy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="rounded-md border border-border bg-surface p-4 text-sm leading-relaxed text-text">
        <div className="mb-1 text-xs uppercase tracking-wide text-text-muted">
          Worked example — ESG and bank RoE
        </div>
        Two banks alike in size, leverage, board and age: one scores 70 on ESG,
        the other 60. Comparing banks, the higher scorer&apos;s RoE is about
        1.0 point higher; comparing only within the same country the gap is
        0.8 points and not reliable; following each bank over time, a 10-point
        rise goes with only 0.45 more RoE points, which cannot be told apart
        from zero.
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// d. Trends
// ---------------------------------------------------------------------------

function TrendsSect({ trends }: { trends: TrendRow[] }) {
  const esgRef = useRef<HTMLDivElement>(null);
  const finRef = useRef<HTMLDivElement>(null);

  const esgCsv = trends.map((t) => ({
    Year: t.Year,
    ESG: t.ESG,
    Environmental: t.E,
    Social: t.S,
    Governance: t.G,
    General: t.General,
  }));
  const finCsv = trends.map((t) => ({
    Year: t.Year,
    "RoA median (Financial)": t["RoA median (Financial)"],
    "RoE median (Financial)": t["RoE median (Financial)"],
    "Tobin's Q median (Financial)": t["Q median (Financial)"],
    "RoA median (Non-financial)": t["RoA median (Non-financial)"],
    "RoE median (Non-financial)": t["RoE median (Non-financial)"],
    "Tobin's Q median (Non-financial)": t["Q median (Non-financial)"],
  }));

  return (
    <section className="flex flex-col gap-4" aria-labelledby="trends-h">
      <h2 id="trends-h" className="font-heading text-lg font-semibold">
        Trends
      </h2>

      <ChartCard
        title="ESG composite &amp; pillars by year"
        description="Mean score across all 65 companies per year (0–100 scale)."
        chartRef={esgRef}
        onExportPng={() =>
          esgRef.current && exportElementAsPng(esgRef.current, "esg_trends.png")
        }
        onExportCsv={() => exportRowsAsCsv(esgCsv, "esg_trends.csv")}
      >
        <div className="h-64 w-full sm:h-80">
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
              <Legend wrapperStyle={{ fontSize: 12, color: "rgb(var(--text-muted))" }} />
              <Line type="monotone" dataKey="ESG" name="Composite" stroke="rgb(var(--accent))" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="E" name="Environmental" stroke="rgb(var(--env))" strokeWidth={2} dot={false} strokeDasharray="4 2" />
              <Line type="monotone" dataKey="S" name="Social" stroke="rgb(var(--soc))" strokeWidth={2} dot={false} strokeDasharray="4 2" />
              <Line type="monotone" dataKey="G" name="Governance" stroke="rgb(var(--gov))" strokeWidth={2} dot={false} strokeDasharray="4 2" />
              <Line type="monotone" dataKey="General" name="General" stroke="rgb(var(--text-muted))" strokeWidth={1.5} dot={false} strokeDasharray="2 3" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </ChartCard>

      <ChartCard
        title="Median RoA, RoE and Tobin's Q by year: financial vs non-financial"
        description="Median within each sector per year."
        chartRef={finRef}
        onExportPng={() =>
          finRef.current && exportElementAsPng(finRef.current, "financial_trends.png")
        }
        onExportCsv={() => exportRowsAsCsv(finCsv, "financial_trends.csv")}
      >
        <div className="h-64 w-full sm:h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trends} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border))" />
              <XAxis dataKey="Year" tick={{ fontSize: 12, fill: "rgb(var(--text-muted))" }} />
              <YAxis yAxisId="left" tick={{ fontSize: 12, fill: "rgb(var(--text-muted))" }}
                label={{ value: "% return", angle: -90, position: "insideLeft", offset: 12, style: { fontSize: 11, fill: "rgb(var(--text-faint))" } }}
              />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12, fill: "rgb(var(--text-muted))" }}
                label={{ value: "Tobin's Q", angle: 90, position: "insideRight", offset: 12, style: { fontSize: 11, fill: "rgb(var(--text-faint))" } }}
              />
              <Tooltip
                contentStyle={{ background: "rgb(var(--surface))", border: "1px solid rgb(var(--border))", borderRadius: "6px", fontSize: 12, color: "rgb(var(--text))" }}
              />
              <Legend wrapperStyle={{ fontSize: 12, color: "rgb(var(--text-muted))" }} />
              <Line yAxisId="left" type="monotone" dataKey="RoA median (Financial)" name="RoA · Financial" stroke="rgb(var(--accent))" strokeWidth={2} dot={false} />
              <Line yAxisId="left" type="monotone" dataKey="RoE median (Financial)" name="RoE · Financial" stroke="rgb(var(--accent))" strokeWidth={2} dot={false} strokeDasharray="5 3" />
              <Line yAxisId="right" type="monotone" dataKey="Q median (Financial)" name="Q · Financial" stroke="rgb(var(--accent))" strokeWidth={1.5} dot={false} strokeDasharray="2 2" />
              <Line yAxisId="left" type="monotone" dataKey="RoA median (Non-financial)" name="RoA · Non-fin" stroke="rgb(var(--env))" strokeWidth={2} dot={false} />
              <Line yAxisId="left" type="monotone" dataKey="RoE median (Non-financial)" name="RoE · Non-fin" stroke="rgb(var(--env))" strokeWidth={2} dot={false} strokeDasharray="5 3" />
              <Line yAxisId="right" type="monotone" dataKey="Q median (Non-financial)" name="Q · Non-fin" stroke="rgb(var(--env))" strokeWidth={1.5} dot={false} strokeDasharray="2 2" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </ChartCard>
    </section>
  );
}

// ---------------------------------------------------------------------------
// e. Descriptive statistics
// ---------------------------------------------------------------------------

function DescriptivesSect({ rows }: { rows: DescriptiveRow[] }) {
  const [group, setGroup] = useState<Group>("All companies");
  const filtered = rows.filter((r) => r.Group === group);
  const csvRows = filtered.map((r) => {
    const { Group: _g, ...rest } = r;
    void _g;
    return rest;
  });

  return (
    <section className="flex flex-col gap-3" aria-labelledby="desc-h">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h2 id="desc-h" className="font-heading text-lg font-semibold">
          Descriptive statistics
        </h2>
        <GroupToggle value={group} options={[...GROUPS]} onChange={setGroup} />
      </div>
      <div className="overflow-x-auto rounded-md border border-border bg-surface">
        <table className="w-full min-w-[640px] text-xs tabular" aria-label="Descriptive statistics">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
              <th className="py-2 pl-4 pr-3 text-left" scope="col">Variable</th>
              <th className="py-2 px-3 text-right" scope="col">N</th>
              <th className="py-2 px-3 text-right" scope="col">Mean</th>
              <th className="py-2 px-3 text-right" scope="col">SD</th>
              <th className="py-2 px-3 text-right" scope="col">Min</th>
              <th className="py-2 px-3 text-right" scope="col">P25</th>
              <th className="py-2 px-3 text-right" scope="col">Median</th>
              <th className="py-2 px-3 text-right" scope="col">P75</th>
              <th className="py-2 pl-3 pr-4 text-right" scope="col">Max</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r, i) => (
              <tr key={i} className="border-b border-border last:border-0">
                <td className="py-1.5 pl-4 pr-3 text-text">{r.Variable}</td>
                <td className="py-1.5 px-3 text-right font-mono text-text-muted">{r.N}</td>
                <td className="py-1.5 px-3 text-right font-mono text-text">{fmt(r.Mean)}</td>
                <td className="py-1.5 px-3 text-right font-mono text-text-muted">{fmt(r.SD)}</td>
                <td className="py-1.5 px-3 text-right font-mono text-text-muted">{fmt(r.Min)}</td>
                <td className="py-1.5 px-3 text-right font-mono text-text-muted">{fmt(r.P25)}</td>
                <td className="py-1.5 px-3 text-right font-mono text-text">{fmt(r.Median)}</td>
                <td className="py-1.5 px-3 text-right font-mono text-text-muted">{fmt(r.P75)}</td>
                <td className="py-1.5 pl-3 pr-4 text-right font-mono text-text-muted">{fmt(r.Max)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div>
        <button
          type="button"
          onClick={() => exportRowsAsCsv(csvRows, `descriptives_${group.replace(/\s+/g, "_").toLowerCase()}.csv`)}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export CSV
        </button>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// f. Correlations: heatmap + full matrix + VIF
// ---------------------------------------------------------------------------

function CorrelationsSect({
  spearman,
  matrix,
  vif,
}: {
  spearman: SpearmanRow[];
  matrix: CorrelationMatrixRow[];
  vif: VifRow[];
}) {
  const [group, setGroup] = useState<Group>("All companies");
  const heatRef = useRef<HTMLDivElement>(null);

  // Build the ESG-vs-financial-measures heatmap: 5 ESG rows × 6 financial cols.
  const ESG_ROWS = ["ESG composite", "Environmental", "Social", "Governance", "General"];
  const lookup = useMemo(() => {
    const m = new Map<string, SpearmanRow>();
    for (const r of spearman.filter((x) => x.Group === group)) {
      m.set(`${r.ESG}||${r.Measure}`, r);
    }
    return m;
  }, [spearman, group]);

  const csvHeat = ESG_ROWS.flatMap((esg) =>
    FIN_MEASURES.map((fin) => {
      const r = lookup.get(`${esg}||${fin}`);
      return {
        Group: group,
        ESG: esg,
        Measure: fin,
        rho: r?.rho ?? null,
        p: r?.p ?? null,
        N: r?.N ?? null,
      };
    }),
  );

  return (
    <section className="flex flex-col gap-4" aria-labelledby="corr-h">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="corr-h" className="font-heading text-lg font-semibold">
            Correlations &amp; multicollinearity
          </h2>
          <p className="mt-0.5 text-xs text-text-muted">
            Spearman ρ for ESG vs the six financial measures. *p&lt;0.05,
            **p&lt;0.01, ***p&lt;0.001.
          </p>
        </div>
        <GroupToggle value={group} options={[...GROUPS]} onChange={setGroup} />
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => heatRef.current && exportElementAsPng(heatRef.current, `corr_heatmap_${group.replace(/\s+/g, "_").toLowerCase()}.png`)}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export PNG
        </button>
        <button
          type="button"
          onClick={() => exportRowsAsCsv(csvHeat, `corr_heatmap_${group.replace(/\s+/g, "_").toLowerCase()}.csv`)}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export CSV
        </button>
      </div>

      <div ref={heatRef} className="overflow-x-auto rounded-md border border-border bg-surface">
        <table className="w-full min-w-[640px] border-collapse text-xs" aria-label="ESG vs financial correlations">
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
            {ESG_ROWS.map((esg) => (
              <tr key={esg} className="border-b border-border last:border-0">
                <th scope="row" className="border-r border-border p-2 text-left text-xs font-medium text-text">
                  {esg}
                </th>
                {FIN_MEASURES.map((fin) => {
                  const r = lookup.get(`${esg}||${fin}`);
                  if (!r)
                    return <td key={fin} className="border-r border-border p-2 last:border-r-0" />;
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
                    >
                      <span className="font-semibold text-text">{r.rho.toFixed(2)}</span>
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

      <h3 className="mt-2 font-heading text-sm font-semibold text-text">
        Full correlation matrix (Pearson, all companies)
      </h3>
      <FullMatrix matrix={matrix} />

      <h3 className="mt-2 font-heading text-sm font-semibold text-text">
        Variance-inflation factors
      </h3>
      <VifTable vif={vif} />
    </section>
  );
}

function FullMatrix({ matrix }: { matrix: CorrelationMatrixRow[] }) {
  const cols =
    matrix.length === 0
      ? []
      : Object.keys(matrix[0]!).filter((k) => k !== "Variable");

  return (
    <div className="overflow-x-auto rounded-md border border-border bg-surface">
      <table className="w-full min-w-[720px] border-collapse text-xs tabular" aria-label="Full correlation matrix">
        <thead>
          <tr>
            <th className="border-b border-r border-border p-2 text-left text-xs font-medium text-text-muted">
              Variable
            </th>
            {cols.map((c) => (
              <th key={c} className="border-b border-r border-border p-2 text-center text-xs font-medium text-text-muted last:border-r-0">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row) => (
            <tr key={row.Variable} className="border-b border-border last:border-0">
              <th scope="row" className="border-r border-border p-2 text-left text-xs font-medium text-text">
                {row.Variable}
              </th>
              {cols.map((c) => {
                const v = row[c];
                if (typeof v !== "number")
                  return <td key={c} className="border-r border-border p-2 last:border-r-0" />;
                const abs = Math.min(Math.abs(v), 1);
                const opacity = Math.round(abs * 60);
                const style =
                  v >= 0
                    ? { backgroundColor: `rgb(var(--accent) / ${opacity}%)` }
                    : { backgroundColor: `rgb(var(--warn) / ${opacity}%)` };
                return (
                  <td
                    key={c}
                    className="border-r border-border p-2 text-center last:border-r-0"
                    style={style}
                  >
                    {v.toFixed(2)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function VifTable({ vif }: { vif: VifRow[] }) {
  return (
    <div className="overflow-x-auto rounded-md border border-border bg-surface">
      <table className="w-full min-w-[320px] text-xs tabular" aria-label="VIF table">
        <thead>
          <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
            <th className="py-2 pl-4 pr-3 text-left" scope="col">Group</th>
            <th className="py-2 px-3 text-left" scope="col">Variable</th>
            <th className="py-2 pl-3 pr-4 text-right" scope="col">VIF</th>
          </tr>
        </thead>
        <tbody>
          {vif.map((r, i) => (
            <tr key={i} className="border-b border-border last:border-0">
              <td className="py-1.5 pl-4 pr-3 text-text-muted">{r.Group}</td>
              <td className="py-1.5 px-3 text-text">{r.Variable}</td>
              <td className="py-1.5 pl-3 pr-4 text-right font-mono text-text">{fmt(r.VIF)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// g. Model choice: Hausman table
// ---------------------------------------------------------------------------

function HausmanSect({ rows }: { rows: HausmanRow[] }) {
  return (
    <section className="flex flex-col gap-3" aria-labelledby="haus-h">
      <h2 id="haus-h" className="font-heading text-lg font-semibold">
        Model choice (Hausman test)
      </h2>
      <p className="text-sm text-text-muted">
        p &lt; 0.05 means the within-company (fixed-effects, B) design is
        preferred over random effects. Otherwise RE is efficient.
      </p>
      <div className="overflow-x-auto rounded-md border border-border bg-surface">
        <table className="w-full min-w-[520px] text-xs tabular" aria-label="Hausman test table">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
              <th className="py-2 pl-4 pr-3 text-left" scope="col">Group</th>
              <th className="py-2 px-3 text-left" scope="col">Measure</th>
              <th className="py-2 px-3 text-right" scope="col">χ²</th>
              <th className="py-2 px-3 text-right" scope="col">df</th>
              <th className="py-2 px-3 text-right" scope="col">p</th>
              <th className="py-2 pl-3 pr-4 text-left" scope="col">Preferred</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-b border-border last:border-0">
                <td className="py-1.5 pl-4 pr-3 text-text-muted">{r.Group}</td>
                <td className="py-1.5 px-3 text-text">{r.Measure}</td>
                <td className="py-1.5 px-3 text-right font-mono text-text">{fmt(r.chi2)}</td>
                <td className="py-1.5 px-3 text-right font-mono text-text-muted">{r.df}</td>
                <td className="py-1.5 px-3 text-right font-mono text-text-muted">{fmtP(r.p)}</td>
                <td className="py-1.5 pl-3 pr-4 text-text">{r.Preferred}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div>
        <button
          type="button"
          onClick={() => exportRowsAsCsv(rows as unknown as Record<string, string | number | null>[], "hausman.csv")}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export CSV
        </button>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// h. Regression results
// ---------------------------------------------------------------------------

function RegressionsSect({ rows }: { rows: RegressionRow[] }) {
  const [group, setGroup] = useState<Group>("All companies");
  const filtered = rows.filter((r) => r.Group === group);
  const byMeasureModel = new Map<string, RegressionRow>();
  for (const r of filtered) {
    byMeasureModel.set(`${r.Measure}||${modelCode(r.Model)}`, r);
  }

  return (
    <section className="flex flex-col gap-3" aria-labelledby="reg-h">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="reg-h" className="font-heading text-lg font-semibold">
            Regression results
          </h2>
          <p className="mt-0.5 text-xs text-text-muted">
            β: change in the dependent per +10 ESG points. SE clustered by
            company. *p&lt;0.05, **p&lt;0.01, ***p&lt;0.001.
          </p>
        </div>
        <GroupToggle value={group} options={[...GROUPS]} onChange={setGroup} />
      </div>

      <div className="overflow-x-auto rounded-md border border-border bg-surface">
        <table className="w-full min-w-[840px] text-xs tabular" aria-label="Regression results">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
              <th className="py-2 pl-4 pr-3 text-left" scope="col">Measure</th>
              {REG_MODELS.map((m) => (
                <th key={m.code} scope="col" className={["py-2 px-3 text-right", m.main ? "bg-accent/10 text-accent" : ""].join(" ")}>
                  {m.label}
                  {m.main && <sup className="ml-0.5 text-[9px]">main</sup>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {FIN_MEASURES.map((measure) => (
              <RegressionRows
                key={measure}
                measure={measure}
                lookup={byMeasureModel}
              />
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-text-faint">
        For IV, the first-stage F is reported below each β; the instrument is
        weak (F &lt; 10 for every measure) so IV estimates are only indicative.
      </p>

      <div>
        <button
          type="button"
          onClick={() =>
            exportRowsAsCsv(
              filtered as unknown as Record<string, string | number | null>[],
              `regressions_${group.replace(/\s+/g, "_").toLowerCase()}.csv`,
            )
          }
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export CSV
        </button>
      </div>
    </section>
  );
}

function RegressionRows({
  measure,
  lookup,
}: {
  measure: FinMeasure;
  lookup: Map<string, RegressionRow>;
}) {
  return (
    <>
      <tr className="border-b border-border last:border-0">
        <td rowSpan={2} className="py-1.5 pl-4 pr-3 text-text">
          {measure}
        </td>
        {REG_MODELS.map((m) => {
          const r = lookup.get(`${measure}||${m.code}`);
          return (
            <td
              key={m.code}
              className={[
                "py-1.5 px-3 text-right font-mono",
                m.main ? "bg-accent/5 text-text" : "text-text",
              ].join(" ")}
            >
              {r ? (
                <>
                  {fmt(r.beta, 3)}
                  <sup>{pStar(r.p)}</sup>
                </>
              ) : (
                "—"
              )}
            </td>
          );
        })}
      </tr>
      <tr className="border-b border-border last:border-0">
        {REG_MODELS.map((m) => {
          const r = lookup.get(`${measure}||${m.code}`);
          return (
            <td
              key={m.code}
              className={[
                "py-1.5 px-3 text-right font-mono text-[10px] text-text-muted",
                m.main ? "bg-accent/5" : "",
              ].join(" ")}
            >
              {r ? (
                <>
                  {fmtP(r.p)}
                  {m.code === "IV" && r.first_stage_F !== null && (
                    <div className="text-[10px] text-text-faint">
                      F={fmt(r.first_stage_F, 1)}
                    </div>
                  )}
                </>
              ) : null}
            </td>
          );
        })}
      </tr>
    </>
  );
}

// ---------------------------------------------------------------------------
// i. Board size and ESG
// ---------------------------------------------------------------------------

function BoardSizeSect({ rows }: { rows: BoardRow[] }) {
  const [group, setGroup] = useState<Group>("All companies");
  const filtered = rows.filter((r) => r.Group === group);

  return (
    <section className="flex flex-col gap-3" aria-labelledby="board-h">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="board-h" className="font-heading text-lg font-semibold">
            Board size and ESG
          </h2>
          <p className="mt-0.5 text-xs text-text-muted">
            Does board size correlate with ESG disclosure? Across companies yes,
            within a company no.
          </p>
        </div>
        <GroupToggle value={group} options={[...GROUPS]} onChange={setGroup} />
      </div>
      <div className="overflow-x-auto rounded-md border border-border bg-surface">
        <table className="w-full min-w-[480px] text-xs tabular" aria-label="Board size vs ESG tests">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
              <th className="py-2 pl-4 pr-3 text-left" scope="col">Test</th>
              <th className="py-2 px-3 text-right" scope="col">β / ρ</th>
              <th className="py-2 px-3 text-right" scope="col">p</th>
              <th className="py-2 pl-3 pr-4 text-right" scope="col">N</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r, i) => (
              <tr key={i} className="border-b border-border last:border-0">
                <td className="py-1.5 pl-4 pr-3 text-text">{r.Test}</td>
                <td className="py-1.5 px-3 text-right font-mono text-text">
                  {fmt(r.beta, 3)}<sup>{pStar(r.p)}</sup>
                </td>
                <td className="py-1.5 px-3 text-right font-mono text-text-muted">
                  {fmtP(r.p)}
                </td>
                <td className="py-1.5 pl-3 pr-4 text-right font-mono text-text-muted">
                  {r.N}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div>
        <button
          type="button"
          onClick={() =>
            exportRowsAsCsv(
              filtered as unknown as Record<string, string | number | null>[],
              `board_size_${group.replace(/\s+/g, "_").toLowerCase()}.csv`,
            )
          }
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Export CSV
        </button>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// j. Comparison with other studies
// ---------------------------------------------------------------------------

function ComparisonSect() {
  return (
    <section className="flex flex-col gap-3" aria-labelledby="comp-h">
      <h2 id="comp-h" className="font-heading text-lg font-semibold">
        Comparison with other studies
      </h2>
      <figure className="rounded-md border border-border bg-surface p-4">
        <img
          src="/fig_study_comparison.png"
          alt="Comparison of ESG–performance effect sizes with earlier studies"
          className="mx-auto h-auto max-w-full"
        />
        <figcaption className="mt-3 text-xs leading-relaxed text-text-muted">
          Across-company (A2) and within-company (B) estimates sit alongside
          comparable papers (Friede et al., 2015; Ferjančič et al., 2024; Khan
          et al., 2016). The direction matches the broader literature; the
          within-company effect in this sample is smaller and not reliably
          different from zero, consistent with a mostly cross-sectional
          association.
        </figcaption>
      </figure>
    </section>
  );
}

// ---------------------------------------------------------------------------
// k. Downloads
// ---------------------------------------------------------------------------

function DownloadsSect() {
  return (
    <section className="flex flex-col gap-3" aria-labelledby="dl-h">
      <h2 id="dl-h" className="font-heading text-lg font-semibold">
        Downloads
      </h2>
      <div className="flex flex-wrap gap-2">
        <a
          href={exportXlsxUrl()}
          download
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Research dataset (Excel)
        </a>
        <a
          href={exportCsvUrl()}
          download
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Research dataset (CSV)
        </a>
        <a
          href="/downloads/ESG_vs_Financials_Results.xlsx"
          download
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Results workbook
        </a>
        <a
          href="/esg_financials_results.json"
          download
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
        >
          Results JSON
        </a>
      </div>
      <p className="text-xs text-text-faint">
        The research dataset has 390 company-years and 21 columns. The results
        workbook holds every table from the analysis.
      </p>
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

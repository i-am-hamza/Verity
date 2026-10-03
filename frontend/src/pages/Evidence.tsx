import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  getEvidence,
  getPrecision,
  postEvidenceReview,
  pdfUrl,
  type EvidenceRow,
} from "../lib/api/client";
import { EmptyState, ErrorState, Loading } from "../components/StateViews";
import { useUrlNumber, useUrlState } from "../hooks/useUrlState";
import { exportRowsAsCsv } from "../lib/export";

export function EvidencePage() {
  const [slug, setSlug] = useUrlState<string>("institution_slug", "");
  const [pillar, setPillar] = useUrlState<string>("pillar", "");
  const [term, setTerm] = useUrlState<string>("term", "");
  const [fy, setFy] = useUrlNumber("fiscal_year", null);
  const [reviewer] = useState<string>(() =>
    typeof window !== "undefined" ? window.localStorage.getItem("verity.reviewer") ?? "reviewer" : "reviewer",
  );
  const [page, setPage] = useState(1);
  const qc = useQueryClient();

  const query = useQuery({
    queryKey: ["evidence", slug, fy, pillar, term, page],
    queryFn: ({ signal }) =>
      getEvidence(
        {
          institution_slug: slug || undefined,
          fiscal_year: fy ?? undefined,
          pillar: pillar || undefined,
          term: term || undefined,
          page,
          page_size: 50,
        },
        signal,
      ),
  });

  const precision = useQuery({
    queryKey: ["precision", "term"],
    queryFn: ({ signal }) => getPrecision("term", signal),
  });

  const mut = useMutation({
    mutationFn: (payload: { evidence_id: number; verdict: "valid" | "false_positive" | "unsure" }) =>
      postEvidenceReview({ ...payload, reviewer }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["evidence"] });
      qc.invalidateQueries({ queryKey: ["precision"] });
    },
  });

  return (
    <section className="flex flex-col gap-4">
      <header>
        <h1 className="font-heading text-2xl font-semibold tracking-tight">Evidence</h1>
        <p className="mt-1 text-sm text-text-muted">
          Match sentences with page refs. Mark each as valid, false positive, or
          unsure; precision tallies below update live.
        </p>
      </header>

      <div className="flex flex-wrap gap-3 rounded-md border border-border bg-surface p-3">
        <input
          type="text"
          placeholder="Institution slug"
          value={slug}
          onChange={(e) => {
            setSlug(e.target.value);
            setPage(1);
          }}
          className="rounded-md border border-border bg-surface-2 px-2 py-1 text-sm"
          aria-label="Filter by institution slug"
        />
        <select
          value={fy ?? ""}
          onChange={(e) => {
            setFy(e.target.value ? Number(e.target.value) : null);
            setPage(1);
          }}
          className="rounded-md border border-border bg-surface-2 px-2 py-1 text-sm"
          aria-label="Filter by fiscal year"
        >
          <option value="">All FYs</option>
          {[2020, 2021, 2022, 2023, 2024, 2025].map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        <select
          value={pillar}
          onChange={(e) => {
            setPillar(e.target.value);
            setPage(1);
          }}
          className="rounded-md border border-border bg-surface-2 px-2 py-1 text-sm"
          aria-label="Filter by pillar"
        >
          <option value="">All pillars</option>
          <option value="Environmental">Environmental</option>
          <option value="Social">Social</option>
          <option value="Governance">Governance</option>
        </select>
        <input
          type="text"
          placeholder="Term"
          value={term}
          onChange={(e) => {
            setTerm(e.target.value);
            setPage(1);
          }}
          className="rounded-md border border-border bg-surface-2 px-2 py-1 text-sm"
          aria-label="Filter by term"
        />
        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            onClick={() =>
              query.data &&
              exportRowsAsCsv(
                query.data.rows
                  .filter((r) => r.reviewed)
                  .map((r) => ({
                    institution_slug: r.institution_slug,
                    fy: r.fiscal_year,
                    pillar: r.pillar,
                    term: r.term_phrase,
                    page: r.page_number,
                    sentence: r.sentence_text,
                    verdict: r.reviewer_verdict ?? "",
                    reviewer: r.reviewer ?? "",
                  })),
                "verity-evidence-reviewed.csv",
              )
            }
            className="rounded-md border border-border bg-surface px-3 py-1 text-xs text-text-muted hover:text-text"
          >
            Export reviewed CSV
          </button>
        </div>
      </div>

      {query.isLoading ? (
        <Loading label="Loading evidence…" />
      ) : query.isError ? (
        <ErrorState message="Could not load evidence." detail={(query.error as Error).message} />
      ) : !query.data || query.data.rows.length === 0 ? (
        <EmptyState title="No match evidence for this filter." />
      ) : (
        <div className="flex flex-col gap-2">
          <div className="text-xs text-text-muted">
            {query.data.total.toLocaleString()} matches · page {query.data.page}
          </div>
          {query.data.rows.map((row) => (
            <EvidenceCard
              key={row.evidence_id}
              row={row}
              onVerdict={(v) => mut.mutate({ evidence_id: row.evidence_id, verdict: v })}
            />
          ))}
          <div className="mt-2 flex items-center justify-between text-xs text-text-muted">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="rounded-md border border-border bg-surface px-2 py-1 disabled:opacity-40"
            >
              Previous
            </button>
            <span>
              page {page} / {Math.max(1, Math.ceil(query.data.total / 50))}
            </span>
            <button
              type="button"
              disabled={page >= Math.ceil(query.data.total / 50)}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-md border border-border bg-surface px-2 py-1 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}

      <section className="rounded-md border border-border bg-surface p-4">
        <h2 className="font-heading text-lg font-semibold">Running precision by term</h2>
        {precision.isLoading ? (
          <Loading />
        ) : (precision.data ?? []).length === 0 ? (
          <EmptyState title="No reviews yet. Mark some matches above to populate precision." />
        ) : (
          <table className="mt-3 w-full text-sm tabular">
            <thead>
              <tr className="text-xs uppercase tracking-wide text-text-muted">
                <th className="px-2 py-1 text-left">term</th>
                <th className="px-2 py-1 text-right">reviewed</th>
                <th className="px-2 py-1 text-right">valid</th>
                <th className="px-2 py-1 text-right">false pos.</th>
                <th className="px-2 py-1 text-right">unsure</th>
                <th className="px-2 py-1 text-right">precision</th>
              </tr>
            </thead>
            <tbody>
              {(precision.data ?? []).map((row) => (
                <tr key={row.term_or_category} className="border-t border-border">
                  <td className="px-2 py-1 text-left">{row.term_or_category}</td>
                  <td className="px-2 py-1 text-right">{row.reviewed}</td>
                  <td className="px-2 py-1 text-right">{row.valid}</td>
                  <td className="px-2 py-1 text-right">{row.false_positive}</td>
                  <td className="px-2 py-1 text-right">{row.unsure}</td>
                  <td className="px-2 py-1 text-right">
                    {row.precision_point === null ? "—" : `${(row.precision_point * 100).toFixed(0)}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </section>
  );
}

function EvidenceCard({
  row,
  onVerdict,
}: {
  row: EvidenceRow;
  onVerdict: (v: "valid" | "false_positive" | "unsure") => void;
}) {
  const highlighted = highlight(row.sentence_text, row.term_phrase);
  return (
    <article className="rounded-md border border-border bg-surface p-3">
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-text-muted">
        <div>
          <span className="font-medium text-text">{row.institution_slug}</span> · FY{row.fiscal_year} ·{" "}
          <span className="rounded-full border border-border bg-surface-2 px-1.5 py-0.5">
            {row.pillar}
          </span>{" "}
          · term <code className="text-text">{row.term_phrase}</code> · page {row.page_number}
        </div>
        <div className="flex items-center gap-1">
          <a
            href={pdfUrl(row.report_id, row.page_number)}
            target="_blank"
            rel="noreferrer"
            className="rounded-md border border-border bg-surface px-2 py-0.5 text-xs hover:text-text"
          >
            Open PDF p.{row.page_number}
          </a>
          {(["valid", "false_positive", "unsure"] as const).map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => onVerdict(v)}
              className={[
                "rounded-md border px-2 py-0.5 text-xs",
                row.reviewer_verdict === v
                  ? "border-accent bg-accent/10 text-accent"
                  : "border-border bg-surface text-text-muted hover:text-text",
              ].join(" ")}
            >
              {v.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>
      <p className="mt-2 text-sm leading-6">{highlighted}</p>
    </article>
  );
}

function highlight(sentence: string, term: string) {
  // Case-insensitive but preserves original casing in the output.
  const re = new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "ig");
  const parts = sentence.split(re);
  return parts.map((p, i) =>
    re.test(p) ? (
      <mark key={i} className="rounded-sm bg-accent/20 px-0.5 text-text">
        {p}
      </mark>
    ) : (
      <span key={i}>{p}</span>
    ),
  );
}

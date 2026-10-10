import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { exportCsvUrl, exportXlsxUrl, getMeta, getMethodology } from "../lib/api/client";
import { EmptyState, ErrorState, Loading } from "../components/StateViews";

export function MethodologyPage() {
  const q = useQuery({
    queryKey: ["methodology"],
    queryFn: ({ signal }) => getMethodology(signal),
  });
  const meta = useQuery({
    queryKey: ["meta"],
    queryFn: ({ signal }) => getMeta(signal),
  });

  if (q.isLoading) return <Loading />;
  if (q.isError) {
    return <ErrorState message="Could not load methodology." detail={(q.error as Error).message} />;
  }
  if (!q.data) return <EmptyState title="No methodology document yet." />;

  return (
    <section className="flex flex-col gap-4">
      {/* Version banner + downloads */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border bg-surface px-4 py-3 text-sm">
        <div className="flex flex-wrap gap-x-5 gap-y-1 text-text-muted">
          {meta.data && (
            <>
              <span>
                Taxonomy{" "}
                <code className="text-[11px] text-text">{meta.data.taxonomy_version.slice(0, 8)}</code>
              </span>
              <span>
                Pipeline{" "}
                <code className="text-[11px] text-text">{meta.data.pipeline_version}</code>
              </span>
              <span>
                Snapshot{" "}
                <span className="text-text">{meta.data.data_snapshot_date}</span>
              </span>
            </>
          )}
        </div>
        <div className="flex gap-2">
          <a
            href={exportXlsxUrl()}
            download
            className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
          >
            Download Excel
          </a>
          <a
            href={exportCsvUrl()}
            download
            className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted hover:text-text"
          >
            Download CSV
          </a>
        </div>
      </div>

      {/* Methodology text */}
      <div className="rounded-md border border-border bg-surface p-6">
        <article className="prose prose-sm max-w-prose text-text prose-headings:font-heading prose-headings:text-text prose-strong:text-text prose-a:text-accent prose-table:text-sm dark:prose-invert [&_table]:w-full [&_table]:border-collapse [&_th]:border [&_th]:border-border [&_th]:bg-surface-2 [&_th]:px-3 [&_th]:py-1.5 [&_th]:text-left [&_th]:text-xs [&_th]:font-semibold [&_th]:uppercase [&_th]:tracking-wide [&_th]:text-text-muted [&_td]:border [&_td]:border-border [&_td]:px-3 [&_td]:py-1.5">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{q.data}</ReactMarkdown>
        </article>
      </div>
    </section>
  );
}

import { useQuery } from "@tanstack/react-query";

import { getBenchmarkStatus } from "../lib/api/client";
import { EmptyState, ErrorState, Loading } from "../components/StateViews";

export function BenchmarkPage() {
  const q = useQuery({
    queryKey: ["benchmark-status"],
    queryFn: ({ signal }) => getBenchmarkStatus(signal),
  });
  if (q.isLoading) return <Loading />;
  if (q.isError) {
    return <ErrorState message="Could not load benchmark status." detail={(q.error as Error).message} />;
  }
  if (!q.data) return <EmptyState title="No benchmark data." />;

  return (
    <section className="flex flex-col gap-4">
      <header>
        <h1 className="font-heading text-2xl font-semibold tracking-tight">
          Benchmark comparison
        </h1>
        <p className="mt-1 text-sm text-text-muted">
          Compare Verity composites against external ESG ratings (MSCI,
          Sustainalytics, LSEG, Bloomberg, …). Upload the agency CSV to begin.
        </p>
      </header>

      {q.data.imported ? (
        <div className="rounded-md border border-border bg-surface p-4">
          <p className="text-sm">
            {q.data.rows.toLocaleString()} benchmark rows imported.
          </p>
        </div>
      ) : (
        <EmptyState
          title={q.data.message}
          action={
            <div className="mx-auto max-w-md rounded-md border border-dashed border-border bg-surface-2 p-6 text-left">
              <h2 className="font-heading text-base font-semibold">Upload CSV</h2>
              <p className="mt-1 text-xs text-text-muted">
                Expected columns:{" "}
                <code>institution_slug, fiscal_year, agency, pillar, rating</code>.
                Server-side validation + row-by-row error reporting is wired in a
                follow-up session; the shell is in place for now.
              </p>
              <form className="mt-3 flex flex-col gap-2">
                <input
                  type="file"
                  accept=".csv"
                  disabled
                  className="text-xs text-text-muted"
                />
                <button
                  type="button"
                  disabled
                  className="rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-text-muted"
                  title="Upload server endpoint lands in Session 8"
                >
                  Upload (disabled — Session 8)
                </button>
              </form>
            </div>
          }
        />
      )}
    </section>
  );
}

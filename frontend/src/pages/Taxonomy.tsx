import { useQuery } from "@tanstack/react-query";

import { getTaxonomy } from "../lib/api/client";
import { EmptyState, ErrorState, Loading } from "../components/StateViews";

export function TaxonomyPage() {
  const q = useQuery({
    queryKey: ["taxonomy-current"],
    queryFn: ({ signal }) => getTaxonomy(signal),
  });
  if (q.isLoading) return <Loading />;
  if (q.isError) {
    return <ErrorState message="Could not load taxonomy." detail={(q.error as Error).message} />;
  }
  if (!q.data) return <EmptyState title="No taxonomy registered yet." />;
  const tax = q.data;

  return (
    <section className="flex flex-col gap-4">
      <header>
        <h1 className="font-heading text-2xl font-semibold tracking-tight">
          Taxonomy — current version
        </h1>
        <p className="mt-1 text-sm text-text-muted">
          Hash <code className="text-text">{tax.hash.slice(0, 16)}…</code> ·
          created {tax.created_at ? tax.created_at.slice(0, 10) : "—"}
        </p>
        <p className="mt-1 text-xs text-text-faint">
          Edits create a new version with a new hash — history is append-only.
          The edit + reprocess UI lands in a follow-up session; this view is
          currently read-only.
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-3">
        {tax.categories.map((cat) => (
          <div key={cat.category_id} className="rounded-md border border-border bg-surface p-4">
            <div className="flex items-center justify-between gap-2">
              <h2 className="font-heading text-base font-semibold">{cat.name}</h2>
              <span className="rounded-full border border-border bg-surface-2 px-2 py-0.5 text-[11px] text-text-muted">
                {cat.pillar}
              </span>
            </div>
            <p className="mt-1 text-xs text-text-muted">
              weight <span className="tabular">{cat.weight.toFixed(2)}</span> ·{" "}
              {cat.terms.length} term{cat.terms.length === 1 ? "" : "s"}
            </p>
            <ul className="mt-3 flex flex-wrap gap-1">
              {cat.terms.map((t) => (
                <li
                  key={t.term_id}
                  className="rounded-full border border-border bg-surface-2 px-2 py-0.5 text-xs text-text-muted"
                  title={`weight ${t.weight.toFixed(2)} · ${t.lemma_based ? "lemma" : "exact"}`}
                >
                  {t.phrase}
                  <span className="ml-1 text-[10px] text-text-faint">
                    {t.weight.toFixed(1)}
                    {t.lemma_based ? "" : "·x"}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

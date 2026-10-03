import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";

import { getMethodology } from "../lib/api/client";
import { EmptyState, ErrorState, Loading } from "../components/StateViews";

export function MethodologyPage() {
  const q = useQuery({
    queryKey: ["methodology"],
    queryFn: ({ signal }) => getMethodology(signal),
  });
  if (q.isLoading) return <Loading />;
  if (q.isError) {
    return <ErrorState message="Could not load methodology." detail={(q.error as Error).message} />;
  }
  if (!q.data) return <EmptyState title="No methodology document yet." />;
  return (
    <section className="rounded-md border border-border bg-surface p-6">
      <article className="prose prose-sm max-w-none text-text prose-headings:text-text prose-strong:text-text prose-a:text-accent dark:prose-invert">
        <ReactMarkdown>{q.data}</ReactMarkdown>
      </article>
    </section>
  );
}

import type { ReactNode } from "react";

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center gap-3 rounded-md border border-border bg-surface p-6 text-text-muted"
    >
      <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-accent" />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({
  title,
  action,
}: {
  title: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-md border border-dashed border-border bg-surface p-8 text-center">
      <p className="text-sm text-text-muted">{title}</p>
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  );
}

export function ErrorState({
  message,
  detail,
}: {
  message: string;
  detail?: string;
}) {
  return (
    <div
      role="alert"
      className="rounded-md border border-warn/40 bg-warn/5 p-5 text-sm"
    >
      <p className="font-semibold text-warn">{message}</p>
      {detail ? (
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words text-xs text-text-muted">
          {detail}
        </pre>
      ) : null}
    </div>
  );
}

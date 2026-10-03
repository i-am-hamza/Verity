import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { getMeta } from "../lib/api/client";
import { useTheme } from "../store/theme";

const nav = [
  { to: "/", label: "Overview" },
  { to: "/coverage", label: "Coverage" },
  { to: "/evidence", label: "Evidence" },
  { to: "/sensitivity", label: "Sensitivity" },
  { to: "/benchmark", label: "Benchmark" },
  { to: "/taxonomy", label: "Taxonomy" },
  { to: "/methodology", label: "Methodology" },
];

export function Layout() {
  const theme = useTheme((s) => s.theme);
  const toggleTheme = useTheme((s) => s.toggle);
  const meta = useQuery({ queryKey: ["meta"], queryFn: ({ signal }) => getMeta(signal) });
  const loc = useLocation();

  return (
    <div className="min-h-screen bg-bg text-text">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded-md focus:bg-accent focus:px-3 focus:py-1.5 focus:text-accent-contrast"
      >
        Skip to content
      </a>
      <header className="sticky top-0 z-30 border-b border-border bg-surface/80 backdrop-blur">
        <div className="mx-auto flex max-w-screen-2xl items-center gap-6 px-4 py-3 sm:px-6">
          <Link
            to="/"
            className="font-heading text-lg font-semibold tracking-tight"
            aria-label="Verity home"
          >
            Verity
          </Link>
          <nav aria-label="Main" className="flex flex-wrap gap-1">
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  [
                    "rounded-md px-3 py-1.5 text-sm transition-colors",
                    isActive
                      ? "bg-surface-2 text-text"
                      : "text-text-muted hover:bg-surface-2 hover:text-text",
                  ].join(" ")
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
              className="rounded-md border border-border bg-surface px-2 py-1 text-xs text-text-muted hover:text-text"
            >
              {theme === "dark" ? "Light" : "Dark"} theme
            </button>
          </div>
        </div>
      </header>

      <main id="main" className="mx-auto max-w-screen-2xl px-4 py-6 sm:px-6">
        <Outlet key={loc.pathname} />
      </main>

      <footer className="mx-auto mt-10 max-w-screen-2xl px-4 pb-6 pt-4 text-xs text-text-faint sm:px-6">
        {meta.data ? (
          <div className="tabular flex flex-wrap items-center gap-x-6 gap-y-1">
            <span>
              taxonomy{" "}
              <code className="text-text-muted">{meta.data.taxonomy_version.slice(0, 12)}…</code>
            </span>
            <span>
              pipeline <code className="text-text-muted">{meta.data.pipeline_version}</code>
            </span>
            <span>snapshot {meta.data.data_snapshot_date}</span>
            <span>
              coverage {meta.data.scored_institutions}/{meta.data.active_institutions} active
              institutions · {meta.data.scored_reports} reports
            </span>
            <span className="text-warn">
              not yet validated against external ratings
            </span>
          </div>
        ) : (
          <div className="opacity-60">loading version metadata…</div>
        )}
      </footer>
    </div>
  );
}

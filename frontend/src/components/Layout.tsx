import { useEffect, useState } from "react";
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
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Close the drawer on route change so a tap on a link doesn't leave the
  // overlay hanging.
  useEffect(() => {
    setDrawerOpen(false);
  }, [loc.pathname]);

  // ESC closes the drawer so keyboard users aren't trapped.
  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setDrawerOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawerOpen]);

  return (
    <div className="min-h-screen bg-bg text-text">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded-md focus:bg-accent focus:px-3 focus:py-1.5 focus:text-accent-contrast"
      >
        Skip to content
      </a>

      <header className="sticky top-0 z-30 border-b border-border bg-surface/80 backdrop-blur">
        <div className="mx-auto flex max-w-screen-2xl items-center gap-3 px-3 py-2 sm:gap-6 sm:px-6 sm:py-3">
          {/* Hamburger — mobile only. 44x44 touch target. */}
          <button
            type="button"
            onClick={() => setDrawerOpen((o) => !o)}
            aria-label={drawerOpen ? "Close navigation" : "Open navigation"}
            aria-expanded={drawerOpen}
            aria-controls="mobile-nav-drawer"
            className="inline-flex h-11 w-11 items-center justify-center rounded-md border border-border bg-surface text-text md:hidden"
          >
            {drawerOpen ? (
              <IconClose />
            ) : (
              <IconHamburger />
            )}
          </button>

          <Link
            to="/"
            className="font-heading text-lg font-semibold tracking-tight"
            aria-label="Verity home"
          >
            Verity
          </Link>

          {/* Desktop nav — collapsed into the drawer below `md`. */}
          <nav aria-label="Main" className="hidden md:flex md:flex-wrap md:gap-1">
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

          <div className="ml-auto flex items-center gap-2 sm:gap-3">
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
              className="inline-flex h-9 items-center rounded-md border border-border bg-surface px-3 text-xs text-text-muted hover:text-text sm:h-11"
            >
              {theme === "dark" ? "Light" : "Dark"}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile drawer. Only mounted when open so the overlay doesn't trap
          clicks on desktop. */}
      {drawerOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-bg/70 backdrop-blur-sm md:hidden"
            aria-hidden="true"
            onClick={() => setDrawerOpen(false)}
          />
          <nav
            id="mobile-nav-drawer"
            aria-label="Mobile navigation"
            className="fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col gap-1 border-r border-border bg-surface p-4 shadow-pop md:hidden"
          >
            <div className="mb-2 flex items-center justify-between">
              <span className="font-heading text-base font-semibold">Verity</span>
              <button
                type="button"
                onClick={() => setDrawerOpen(false)}
                aria-label="Close navigation"
                className="inline-flex h-11 w-11 items-center justify-center rounded-md border border-border bg-surface text-text"
              >
                <IconClose />
              </button>
            </div>
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  [
                    "flex min-h-[44px] items-center rounded-md px-3 text-base transition-colors",
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
        </>
      )}

      <main id="main" className="mx-auto max-w-screen-2xl px-3 py-5 sm:px-6 sm:py-6">
        <Outlet key={loc.pathname} />
      </main>

      <footer className="mx-auto mt-10 max-w-screen-2xl px-3 pb-6 pt-4 text-xs text-text-faint sm:px-6">
        {meta.data ? (
          <div className="tabular flex flex-col gap-1 sm:flex-row sm:flex-wrap sm:items-center sm:gap-x-6">
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

function IconHamburger() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
      <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function IconClose() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
      <path d="M5 5l10 10M15 5L5 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

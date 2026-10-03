import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { Loading } from "./components/StateViews";

/**
 * Route-level code-split. Session 7 shipped the whole dashboard as one
 * ~908 kB chunk; lazy()-ing each page means the Overview landing load
 * only pays for Overview + layout + Recharts-shared, with the heavier
 * views (Sensitivity has the scatter + error bars, Institution has
 * radar + lines + bars) loading on navigation. Noticeably helps on
 * mobile 4G where every KB counts.
 */
const OverviewPage = lazy(() =>
  import("./pages/Overview").then((m) => ({ default: m.OverviewPage })),
);
const InstitutionPage = lazy(() =>
  import("./pages/Institution").then((m) => ({ default: m.InstitutionPage })),
);
const CoveragePage = lazy(() =>
  import("./pages/Coverage").then((m) => ({ default: m.CoveragePage })),
);
const EvidencePage = lazy(() =>
  import("./pages/Evidence").then((m) => ({ default: m.EvidencePage })),
);
const SensitivityPage = lazy(() =>
  import("./pages/Sensitivity").then((m) => ({ default: m.SensitivityPage })),
);
const BenchmarkPage = lazy(() =>
  import("./pages/Benchmark").then((m) => ({ default: m.BenchmarkPage })),
);
const TaxonomyPage = lazy(() =>
  import("./pages/Taxonomy").then((m) => ({ default: m.TaxonomyPage })),
);
const MethodologyPage = lazy(() =>
  import("./pages/Methodology").then((m) => ({ default: m.MethodologyPage })),
);

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route
          index
          element={
            <Suspense fallback={<Loading label="Loading view…" />}>
              <OverviewPage />
            </Suspense>
          }
        />
        <Route
          path="institution/:slug"
          element={
            <Suspense fallback={<Loading label="Loading institution…" />}>
              <InstitutionPage />
            </Suspense>
          }
        />
        <Route
          path="coverage"
          element={
            <Suspense fallback={<Loading label="Loading coverage…" />}>
              <CoveragePage />
            </Suspense>
          }
        />
        <Route
          path="evidence"
          element={
            <Suspense fallback={<Loading label="Loading evidence…" />}>
              <EvidencePage />
            </Suspense>
          }
        />
        <Route
          path="sensitivity"
          element={
            <Suspense fallback={<Loading label="Loading sensitivity…" />}>
              <SensitivityPage />
            </Suspense>
          }
        />
        <Route
          path="benchmark"
          element={
            <Suspense fallback={<Loading label="Loading benchmark…" />}>
              <BenchmarkPage />
            </Suspense>
          }
        />
        <Route
          path="taxonomy"
          element={
            <Suspense fallback={<Loading label="Loading taxonomy…" />}>
              <TaxonomyPage />
            </Suspense>
          }
        />
        <Route
          path="methodology"
          element={
            <Suspense fallback={<Loading label="Loading methodology…" />}>
              <MethodologyPage />
            </Suspense>
          }
        />
      </Route>
    </Routes>
  );
}

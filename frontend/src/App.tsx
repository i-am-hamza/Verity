import { Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { OverviewPage } from "./pages/Overview";
import { InstitutionPage } from "./pages/Institution";
import { CoveragePage } from "./pages/Coverage";
import { EvidencePage } from "./pages/Evidence";
import { SensitivityPage } from "./pages/Sensitivity";
import { BenchmarkPage } from "./pages/Benchmark";
import { TaxonomyPage } from "./pages/Taxonomy";
import { MethodologyPage } from "./pages/Methodology";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<OverviewPage />} />
        <Route path="institution/:slug" element={<InstitutionPage />} />
        <Route path="coverage" element={<CoveragePage />} />
        <Route path="evidence" element={<EvidencePage />} />
        <Route path="sensitivity" element={<SensitivityPage />} />
        <Route path="benchmark" element={<BenchmarkPage />} />
        <Route path="taxonomy" element={<TaxonomyPage />} />
        <Route path="methodology" element={<MethodologyPage />} />
      </Route>
    </Routes>
  );
}

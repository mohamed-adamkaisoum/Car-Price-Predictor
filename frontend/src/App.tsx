import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { DealPage } from "./pages/DealPage";
import { HomePage } from "./pages/HomePage";
import { MarketPage } from "./pages/MarketPage";
import { SearchPage } from "./pages/SearchPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="recherche" element={<SearchPage />} />
          <Route path="analyse" element={<DealPage />} />
          <Route path="marche" element={<MarketPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

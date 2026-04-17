import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import ConfigList from "./pages/ConfigList";
import ConfigEdit from "./pages/ConfigEdit";
import RunDetail from "./pages/RunDetail";
import Settings from "./pages/Settings";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/configs" element={<ConfigList />} />
        <Route path="/configs/new" element={<ConfigEdit />} />
        <Route path="/configs/:id" element={<ConfigEdit />} />
        <Route path="/runs/:id" element={<RunDetail />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import RunDetail from "./pages/RunDetail";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/runs/:runId" element={<RunDetail />} />
    </Routes>
  );
}

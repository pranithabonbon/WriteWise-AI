import { Route, Routes } from "react-router-dom";

import Home from "./pages/Home.jsx";
import History from "./pages/History.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/history" element={<History />} />
      <Route path="/history/:id" element={<History />} />
    </Routes>
  );
}

import { Routes, Route } from "react-router-dom";
import { useEffect, useState } from "react";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";

export default function App() {
  const [theme, setTheme] = useState("dark");

  useEffect(() => {
    document.body.setAttribute("data-theme", theme);
  }, [theme]);

  return (
    <Routes>
      <Route path="/" element={<Home theme={theme} setTheme={setTheme} />} />
      <Route path="/dashboard" element={<Dashboard theme={theme} setTheme={setTheme} />} />
      <Route path="*" element={<Home theme={theme} setTheme={setTheme} />} />
    </Routes>
  );
}

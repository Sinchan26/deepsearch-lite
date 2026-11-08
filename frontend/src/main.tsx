import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

function Foundation() {
  return <main className="mx-auto max-w-2xl p-8"><h1 className="text-3xl font-semibold">DeepResearch Lite</h1><p className="mt-4">Foundation ready. Research and the research workspace are planned for subsequent phases.</p></main>;
}

createRoot(document.getElementById("root")!).render(<StrictMode><Foundation /></StrictMode>);

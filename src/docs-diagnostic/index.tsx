import { createRoot } from "react-dom/client";
import { App } from "./App";

const root = document.getElementById("docs-diagnostic-root");
if (root) {
  createRoot(root).render(<App />);
}

import "@fontsource-variable/archivo/wdth.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles/tokens.css";
import "./styles/nemo.css";
import "./styles/screens/a.css";
import "./styles/screens/b.css";
import "./styles/screens/c.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

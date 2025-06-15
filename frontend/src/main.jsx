import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import ErrorBoundary from "./components/ErrorBoundary";
import "./styles/index.css";

console.warn = (msg) => {
  if (
    msg.includes("React Router will begin wrapping state updates") ||
    msg.includes("Download the React DevTools for a better development experience: https://reactjs.org/link/react-devtools") ||
    msg.includes("Relative route resolution within Splat routes is changing")
  ) return;
  console.log(msg);
};

ReactDOM.createRoot(document.getElementById("root")).render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);

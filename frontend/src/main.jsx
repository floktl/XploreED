import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./styles/index.css";

// Silence logs in production; keep console.error
(() => {
  const isDev = import.meta.env.VITE_ENV === "development" || import.meta.env.MODE === "development";
  if (!isDev) {
    const noop = () => {};
    console.log = noop;
    console.info = noop;
    console.debug = noop;
    // Keep warnings minimal except critical ones
    const origWarn = console.warn;
    console.warn = (msg, ...rest) => {
      const text = String(msg || "");
      // Allow only security/network warnings
      if (/deprecated|security|csrf|cors|network|unauthorized/i.test(text)) {
        origWarn.call(console, msg, ...rest);
      }
      // otherwise suppress
    };
  } else {
    // In development, filter a few noisy warnings
    const origWarn = console.warn;
    console.warn = (msg, ...rest) => {
      const text = String(msg || "");
      if (
        text.includes("React Router will begin wrapping state updates") ||
        text.includes("Download the React DevTools for a better development experience:") ||
        text.includes("Relative route resolution within Splat routes is changing")
      ) return;
      origWarn.call(console, msg, ...rest);
    };
  }
})();

ReactDOM.createRoot(document.getElementById("root")).render(
    <App />
);


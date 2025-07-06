import React from "react";

export default function Footer({ children }) {
  return (
    <footer
      className="fixed bottom-0 left-0 w-full px-4 py-2 z-50 flex items-center justify-between border-t border-white/10 backdrop-blur-md bg-white/10 text-xs text-white/90"
    >
      <div className="flex items-center gap-2">{children}</div>
      <span className="tracking-wide opacity-80 drop-shadow-sm">© 2025 Flo's Lessons</span>
    </footer>
  );
}

import React from "react";

export default function Footer() {
  return (
    <footer
      className="fixed bottom-2 right-2 px-4 h-7 z-50 rounded-full shadow-sm border border-white/10
      backdrop-blur-md bg-white/10 text-xs text-white/90 flex items-center justify-center
      transition-all duration-300 hover:brightness-110"
    >
      <span className="tracking-wide opacity-80 drop-shadow-sm">© 2025 Flo's Lessons</span>
    </footer>
  );
}

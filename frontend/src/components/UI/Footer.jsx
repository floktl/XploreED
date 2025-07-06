import React from "react";

export default function Footer() {
  return (
    <footer
      className="fixed bottom-0 w-full h-10 z-40 backdrop-blur-sm text-white text-xs flex items-center justify-center
      bg-gradient-to-r from-blue-500 via-blue-600 to-blue-800/80"
    >
      <span className="opacity-80">© 2025 Flo's Lessons</span>
    </footer>
  );
}

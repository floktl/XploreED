import React, { useState } from "react";
import AskAiModal from "./AskAiModal";

function AskAiButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        data-tour="help"
        className="fixed bottom-6 right-6 z-50 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg px-5 py-3 text-lg font-bold transition-all"
        style={{ boxShadow: "0 4px 24px rgba(0,0,0,0.15)" }}
        title="Ask AI or get help"
        onClick={() => setOpen(true)}
      >
        M
      </button>
      {open && <AskAiModal onClose={() => setOpen(false)} />}
    </>
  );
}

export default AskAiButton;

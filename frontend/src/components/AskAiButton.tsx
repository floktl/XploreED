import React, { useState } from "react";
import AskAiModal from "./AskAiModal";
import useAppStore from "../store/useAppStore";

export default function AskAiButton() {
    const [open, setOpen] = useState(false);
    const darkMode = useAppStore((s) => s.darkMode);

    return (
        <>
            <button
                onClick={() => setOpen(true)}
                className={`fixed bottom-20 right-4 z-50 w-14 h-14 rounded-full flex items-center justify-center shadow-lg hover:opacity-90 ${darkMode ? "bg-blue-700 text-white" : "bg-blue-600 text-white"}`}
            >
                <svg viewBox="0 0 100 100" className="w-8 h-8" fill="currentColor" stroke="currentColor" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 80 V20 L50 60 L80 20 V80" fill="none" />
                </svg>
            </button>
            {open && <AskAiModal onClose={() => setOpen(false)} />}
        </>
    );
}

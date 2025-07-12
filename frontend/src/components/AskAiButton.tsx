import React, { useState, useRef } from "react";
import AskAiModal from "./AskAiModal";
import useAppStore from "../store/useAppStore";

export default function AskAiButton() {
    const [open, setOpen] = useState(false);
    const darkMode = useAppStore((s) => s.darkMode);
    const btnRef = useRef<HTMLButtonElement>(null);
    const [btnRect, setBtnRect] = useState<DOMRect | null>(null);

    const handleOpen = () => {
        if (btnRef.current) {
            setBtnRect(btnRef.current.getBoundingClientRect());
        }
        setOpen(true);
    };

    return (
        <>
            <button
                ref={btnRef}
                onClick={handleOpen}
                className={`fixed bottom-20 right-4 z-50 w-11 h-11 rounded-full flex items-center justify-center shadow-lg bg-white/80 hover:bg-white text-blue-700 border border-blue-200 transition-all duration-150`}
                style={{ boxShadow: '0 2px 12px 0 rgba(80,120,200,0.10)' }}
            >
                {/* Simple assistant SVG icon */}
                <svg viewBox="0 0 40 40" className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="20" cy="20" r="12" fill="#e3eafc" stroke="#1a237e" strokeWidth="1.5" />
                  <ellipse cx="20" cy="27" rx="6" ry="2.5" fill="#b3c6ff" />
                  <circle cx="15.5" cy="18" r="1.5" fill="#1a237e" />
                  <circle cx="24.5" cy="18" r="1.5" fill="#1a237e" />
                  <rect x="17" y="22" width="6" height="2" rx="1" fill="#1a237e" />
                  <rect x="18.5" y="10" width="3" height="3" rx="1.5" fill="#b3c6ff" stroke="#1a237e" />
                  <rect x="10" y="16" width="2" height="6" rx="1" fill="#b3c6ff" stroke="#1a237e" />
                  <rect x="28" y="16" width="2" height="6" rx="1" fill="#b3c6ff" stroke="#1a237e" />
                </svg>
            </button>
            {open && <AskAiModal onClose={() => setOpen(false)} btnRect={btnRect} />}
        </>
    );
}

import React, { useState, useRef } from "react";
import AskAiModal from "./AskAiModal";
import useAppStore from "../store/useAppStore";
import Footer from "./UI/Footer";
import { useLocation } from "react-router-dom";

export default function AskAiButton() {
    const [open, setOpen] = useState(false);
    const darkMode = useAppStore((s) => s.darkMode);
    const btnRef = useRef<HTMLButtonElement>(null);
    const [btnRect, setBtnRect] = useState<DOMRect | null>(null);
    const [bottomOffset, setBottomOffset] = useState(4);
    const footerVisible = useAppStore((s) => s.footerVisible);
    const location = useLocation();

    React.useEffect(() => {
        if (location.pathname === "/menu") {
            setBottomOffset(8);
        } else {
            setBottomOffset(footerVisible ? 56 : 8);
        }
    }, [footerVisible, location.pathname]);

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
                className={`fixed right-4 z-50 w-14 h-14 rounded-full flex items-center justify-center shadow-lg border transition-all duration-200
                    ${darkMode
                        ? 'bg-gradient-to-br from-indigo-800/90 via-blue-900/90 to-blue-800/80 border-blue-700 ring-2 ring-blue-700/40 hover:ring-4 hover:scale-105 drop-shadow-[0_0_16px_rgba(56,189,248,0.25)]'
                        : 'bg-white/80 hover:bg-white text-blue-700 border border-blue-200'}
                `}
                style={{
                    bottom: bottomOffset,
                    ...(darkMode ? {
                        boxShadow: '0 4px 24px 0 rgba(56,189,248,0.18), 0 1.5px 8px 0 rgba(30,32,40,0.18)',
                        backdropFilter: 'blur(6px)',
                        WebkitBackdropFilter: 'blur(6px)',
                    } : {
                        boxShadow: '0 2px 12px 0 rgba(80,120,200,0.10)'
                    })
                }}
            >
                {/* Modern assistant SVG icon */}
                <svg viewBox="0 0 40 40" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
                    style={darkMode ? { filter: 'drop-shadow(0 0 8px #38bdf8cc)' } : {}}>
                    <circle cx="20" cy="20" r="12" fill={darkMode ? "#1e293b" : "#e3eafc"} stroke="#38bdf8" strokeWidth="1.5" />
                    <ellipse cx="20" cy="27" rx="6" ry="2.5" fill={darkMode ? "#2563eb" : "#b3c6ff"} />
                    <circle cx="15.5" cy="18" r="1.5" fill="#38bdf8" />
                    <circle cx="24.5" cy="18" r="1.5" fill="#38bdf8" />
                    <rect x="17" y="22" width="6" height="2" rx="1" fill="#38bdf8" />
                    <rect x="18.5" y="10" width="3" height="3" rx="1.5" fill="#2563eb" stroke="#38bdf8" />
                    <rect x="10" y="16" width="2" height="6" rx="1" fill="#2563eb" stroke="#38bdf8" />
                    <rect x="28" y="16" width="2" height="6" rx="1" fill="#2563eb" stroke="#38bdf8" />
                </svg>
            </button>
            {open && <AskAiModal onClose={() => setOpen(false)} btnRect={btnRect} />}
        </>
    );
}

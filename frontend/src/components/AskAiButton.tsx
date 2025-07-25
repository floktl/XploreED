import React, { useState, useRef } from "react";
import AskAiModal from "./AskAiModal";
import useAppStore from "../store/useAppStore";
import Footer from "./UI/Footer";
import { useLocation } from "react-router-dom";

export default function AskAiButton() {
    const [open, setOpen] = useState(false);
    const darkMode = useAppStore((s) => s.darkMode);
    const debugEnabled = useAppStore((s) => s.debugEnabled);
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

    // Debug button logic
    const handleDebug = async () => {
        try {
            const response = await fetch('/api/debug/ai-user-titles', { method: 'POST', credentials: 'include' });
            if (!response.ok) throw new Error('Failed to trigger backend debug');
            console.log('Triggered backend debug for ai_user_data titles.');
        } catch (err) {
            console.error('Debug fetch error:', err);
        }
    };

    return (
        <>
            <div
                style={{
                    position: "fixed",
                    right: 16,
                    bottom: bottomOffset,
                    zIndex: 1000,
                    display: open ? "none" : "flex",
                    flexDirection: "row",
                    gap: 8,
                }}
            >
                <button
                    ref={btnRef}
                    onClick={handleOpen}
                    className={`rounded-full shadow-lg p-3 transition-all duration-200 ${darkMode ? "bg-blue-700 hover:bg-blue-800" : "bg-blue-600 hover:bg-blue-700"}`}
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
                {debugEnabled && (
                    <button
                        onClick={handleDebug}
                        className={`rounded-full shadow-lg px-4 py-2 font-semibold text-white transition-all duration-200 ${darkMode ? "bg-gray-700 hover:bg-gray-800" : "bg-gray-600 hover:bg-gray-700"}`}
                    >
                        Debug
                    </button>
                )}
            </div>
            {open && (
                <AskAiModal onClose={() => setOpen(false)} btnRect={btnRect} />
            )}
        </>
    );
}

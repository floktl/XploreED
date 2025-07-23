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
                    display: "flex",
                    flexDirection: "row",
                    gap: 8,
                }}
            >
                <button
                    ref={btnRef}
                    onClick={handleOpen}
                    className={`rounded-full shadow-lg px-4 py-2 font-semibold text-white transition-all duration-200 ${darkMode ? "bg-blue-700 hover:bg-blue-800" : "bg-blue-600 hover:bg-blue-700"}`}
                >
                    Ask Mistral
                </button>
                <button
                    onClick={handleDebug}
                    className={`rounded-full shadow-lg px-4 py-2 font-semibold text-white transition-all duration-200 ${darkMode ? "bg-gray-700 hover:bg-gray-800" : "bg-gray-600 hover:bg-gray-700"}`}
                >
                    Debug
                </button>
            </div>
            {open && (
                <AskAiModal onClose={() => setOpen(false)} btnRect={btnRect} />
            )}
        </>
    );
}

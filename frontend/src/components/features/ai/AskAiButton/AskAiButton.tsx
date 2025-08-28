import React, { useState, useRef } from "react";
import AskAiModal from "../AskAiModal/AskAiModal";
import useAppStore from "../../../../store/useAppStore";
import { useLocation } from "react-router-dom";
import AIAssistantIcon from "./Components/AIAssistantIcon";
import { triggerBackendDebug } from "./Utils/debugUtils";

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

    return (
        <>
            {!open && (
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
                        className={`rounded-full shadow-lg p-3 transition-all duration-200 ${darkMode ? "bg-blue-700 hover:bg-blue-800" : "bg-blue-600 hover:bg-blue-700"}`}
                    >
                        <AIAssistantIcon darkMode={darkMode} />
                    </button>
                    {debugEnabled && (
                        <button
                            onClick={triggerBackendDebug}
                            className={`rounded-full shadow-lg px-4 py-2 font-semibold text-white transition-all duration-200 ${darkMode ? "bg-gray-700 hover:bg-gray-800" : "bg-gray-600 hover:bg-gray-700"}`}
                        >
                            Debug
                        </button>
                    )}
                </div>
            )}
            {open && (
                <AskAiModal onClose={() => setOpen(false)} btnRect={btnRect} />
            )}
        </>
    );
}

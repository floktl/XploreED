import React from "react";

interface AIAssistantIconProps {
    darkMode: boolean;
}

export default function AIAssistantIcon({ darkMode }: AIAssistantIconProps) {
    return (
        <svg
            viewBox="0 0 40 40"
            className="w-8 h-8"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={darkMode ? { filter: 'drop-shadow(0 0 8px #38bdf8cc)' } : {}}
        >
            <circle cx="20" cy="20" r="12" fill={darkMode ? "#1e293b" : "#e3eafc"} stroke="#38bdf8" strokeWidth="1.5" />
            <ellipse cx="20" cy="27" rx="6" ry="2.5" fill={darkMode ? "#2563eb" : "#b3c6ff"} />
            <circle cx="15.5" cy="18" r="1.5" fill="#38bdf8" />
            <circle cx="24.5" cy="18" r="1.5" fill="#38bdf8" />
            <rect x="17" y="22" width="6" height="2" rx="1" fill="#38bdf8" />
            <rect x="18.5" y="10" width="3" height="3" rx="1.5" fill="#2563eb" stroke="#38bdf8" />
            <rect x="10" y="16" width="2" height="6" rx="1" fill="#2563eb" stroke="#38bdf8" />
            <rect x="28" y="16" width="2" height="6" rx="1" fill="#2563eb" stroke="#38bdf8" />
        </svg>
    );
}

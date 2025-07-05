import React from "react";
import { useNavigate } from "react-router-dom";
import useAppStore from "../../store/useAppStore";
import Badge from "./Badge";

export default function Header() {
    const navigate = useNavigate();
    const username = useAppStore((state) => state.username);
    const darkMode = useAppStore((state) => state.darkMode);
    const isAdmin = useAppStore((state) => state.isAdmin);
    const avatarLetter = username ? username.charAt(0).toUpperCase() : "?";
    const currentLevel = useAppStore((state) => state.currentLevel ?? 0);

    const maxLevel = 10;
    const percentage = Math.min(100, Math.round((currentLevel / maxLevel) * 100));
    const radius = 14;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
        <header
            className={`fixed top-0 w-full z-50 shadow-md backdrop-blur-sm ${darkMode
                ? "bg-gray-800/80 text-white"
                : "bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white"
                }`}
        >
            <div className="max-w-5xl mx-auto flex items-center justify-between px-4 py-3">
                <h1
                    className="text-xl font-semibold tracking-wide cursor-pointer"
                    onClick={() => navigate("/menu")}
                >
                    Flo's-Lessons.com
                </h1>

                {!isAdmin && username && (
                    <div className="flex items-center gap-2 bg-gray-900 px-3 py-1 rounded-full">
                        <button
                            onClick={() => navigate("/profile")}
                            className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-semibold"
                        >
                            {avatarLetter}
                        </button>
                        <div className="w-8 h-8 relative">
                            <svg width="32" height="32">
                                <circle
                                    cx="16"
                                    cy="16"
                                    r={radius}
                                    stroke="#4B5563"
                                    strokeWidth="2"
                                    fill="none"
                                />
                                <circle
                                    cx="16"
                                    cy="16"
                                    r={radius}
                                    stroke="#10B981"
                                    strokeWidth="2"
                                    fill="none"
                                    strokeLinecap="round"
                                    strokeDasharray={`${circumference} ${circumference}`}
                                    strokeDashoffset={strokeDashoffset}
                                    transform="rotate(-90 16 16)"
                                />
                                <text
                                    x="16"
                                    y="16"
                                    textAnchor="middle"
                                    dy=".3em"
                                    fontSize="10"
                                    fill="#ffffff"
                                    fontWeight="bold"
                                >
                                    {currentLevel}
                                </text>
                            </svg>
                        </div>
                    </div>

                )}
            </div>
        </header>
    );
}

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
    const currentLevel = useAppStore((state) => state.currentLevel);

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
                <div className="flex items-center gap-2">
                    {!isAdmin && <Badge type="default">Student</Badge>}
                    {!isAdmin && (
                        <span className="text-sm font-medium">Level {currentLevel ?? 0}</span>
                    )}
                    {!isAdmin && username && (
                        <button
                            onClick={() => navigate("/profile")}
                            className="w-9 h-9 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold"
                        >
                            {avatarLetter}
                        </button>
                    )}
                </div>
            </div>
        </header>
    );
}

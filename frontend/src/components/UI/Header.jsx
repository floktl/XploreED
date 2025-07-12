import React from "react";
import { useNavigate } from "react-router-dom";
import {
    Settings,
    LogOut,
    Moon,
    Sun,
    Mail,
    Menu,
    FileText,
    Brain,
    BookText,
    Archive,
} from "lucide-react";
import useAppStore from "../../store/useAppStore";
import Dropdown from "./Dropdown";

export default function Header({ minimal = false }) {
    const navigate = useNavigate();
    const username = useAppStore((state) => state.username);
    const darkMode = useAppStore((state) => state.darkMode);
    const toggleDarkMode = useAppStore((state) => state.toggleDarkMode);
    const isAdmin = useAppStore((state) => state.isAdmin);
    const currentLevel = useAppStore((state) => state.currentLevel ?? 0);
    const avatarLetter = username ? username.charAt(0).toUpperCase() : "?";

    const handleLogout = () => {
        localStorage.removeItem("username");
        useAppStore.getState().resetStore();
        navigate("/");
    };

    const maxLevel = 10;
    const percentage = Math.min(100, Math.round((currentLevel / maxLevel) * 100));
    const radius = 14;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
        <header
            className={`fixed top-0 w-full z-50 shadow-md backdrop-blur-sm ${darkMode
                ? "bg-gray-800/80 text-white"
                : "bg-gradient-to-r from-blue-500 via-blue-600 to-blue-900 text-white"
                }`}
        >
            <div className="max-w-5xl mx-auto flex items-center justify-between px-4 py-3">
                <h1
                    className="text-xl font-semibold tracking-wide cursor-pointer"
                    onClick={() => navigate("/menu")}
                >
                    @XplorED
                </h1>
                {!minimal && username && (
                    <div className="flex items-center gap-4">
                        {/* Brain dropdown */}
                        {!isAdmin && (
                            <Dropdown
                                trigger={
                                    <div className="p-2 rounded-full bg-black/20 hover:bg-black/30 transition cursor-pointer">
                                        <Brain className="w-5 h-5 text-white" />
                                    </div>
                                }
                            >
                                <button
                                    onClick={() => navigate("/vocabulary")}
                                    className="flex items-center w-full gap-2 px-4 py-3 text-sm text-gray-800 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-gray-800 transition"
                                >
                                    <BookText className="w-4 h-4" />
                                    Vocabulary
                                </button>
                                <button
                                    onClick={() => navigate("/topic-memory")}
                                    className="flex items-center w-full gap-2 px-4 py-3 text-sm text-gray-800 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-gray-800 transition"
                                >
                                    <Archive className="w-4 h-4" />
                                    Topic Memory
                                </button>
                                <button
                                    onClick={() => navigate("/grammar-map")}
                                    className="flex items-center w-full gap-2 px-4 py-3 text-sm text-gray-800 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-gray-800 transition"
                                >
                                    <Brain className="w-4 h-4" />
                                    Grammar Map
                                </button>
                            </Dropdown>
                        )}
                        {/* Profile dropdown */}
                        <Dropdown
                            trigger={
                                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-black/20 hover:bg-black/30 transition cursor-pointer">
                                    <span className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-semibold">
                                        {avatarLetter}
                                    </span>
                                    {!isAdmin && (
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
                                    )}
                                </div>
                            }
                        >
                            {!isAdmin && (
                                <>
                                    <button
                                        onClick={() => navigate("/profile")}
                                        className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-800 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-gray-800 transition w-full text-left"
                                    >
                                        <span className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-semibold">
                                            {avatarLetter}
                                        </span>
                                        Profile
                                    </button>
                                    <button
                                        onClick={() => navigate("/menu")}
                                        className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-800 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-gray-800 transition w-full text-left"
                                    >
                                        <Menu className="w-4 h-4" />
                                        Main Menu
                                    </button>
                                </>
                            )}
                            <button
                                onClick={() => navigate("/settings")}
                                className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-800 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-gray-800 transition w-full text-left"
                            >
                                <Settings className="w-4 h-4" />
                                Settings
                            </button>
                            <button
                                onClick={toggleDarkMode}
                                className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-800 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-gray-800 transition w-full text-left"
                            >
                                {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                                {darkMode ? "Light Mode" : "Dark Mode"}
                            </button>
                            <button
                                onClick={() => navigate("/support")}
                                className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-800 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-gray-800 transition w-full text-left"
                            >
                                <Mail className="w-4 h-4" />
                                Support
                            </button>
                            <button
                                onClick={() => navigate("/terms-of-service")}
                                className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-800 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-gray-800 transition w-full text-left"
                            >
                                <FileText className="w-4 h-4" />
                                Terms of Service
                            </button>
                            <button
                                onClick={() => navigate("/about")}
                                className="flex items-center gap-3 px-4 py-3 text-sm font-medium text-gray-800 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-gray-800 transition w-full text-left"
                            >
                                <Menu className="w-4 h-4" />
                                About
                            </button>
                            <button
                                onClick={handleLogout}
                                className="flex items-center gap-3 px-4 py-3 text-sm font-semibold text-red-600 hover:bg-red-50 dark:hover:bg-red-900/40 dark:text-red-400 transition w-full text-left"
                            >
                                <LogOut className="w-4 h-4" />
                                Logout
                            </button>
                        </Dropdown>
                    </div>
                )}
            </div>
        </header>
    );
}

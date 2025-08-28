
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
import useAppStore from "../../../store/useAppStore";
import Dropdown from "./Dropdown";
import Spinner from "./Spinner";
import { debugDeleteUserData } from "../../../services/api";
import Modal from "./Modal";

export default function Header({ minimal = false }) {
    const navigate = useNavigate();
    const username = useAppStore((state) => state.username);
    const darkMode = useAppStore((state) => state.darkMode);
    const toggleDarkMode = useAppStore((state) => state.toggleDarkMode);
    const isAdmin = useAppStore((state) => state.isAdmin);
    const currentLevel = useAppStore((state) => state.currentLevel ?? 0);
    const avatarLetter = username ? username.charAt(0).toUpperCase() : "?";
    const backgroundActivity = useAppStore((state) => state.backgroundActivity);
    const debugEnabled = useAppStore((state) => state.debugEnabled);
    const [showActivity, setShowActivity] = React.useState(false);
    const [showDebugModal, setShowDebugModal] = React.useState(false);
    const [debugResult, setDebugResult] = React.useState(null);

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
                <div className="flex items-center gap-4">
                    {/* Only the main brain button with spinner, styled as a round button */}
                    {!isAdmin && (
                        <Dropdown
                            trigger={
                                <div className="p-2 rounded-full bg-black/20 hover:bg-black/30 transition cursor-pointer relative flex items-center justify-center">
                                    <span className="relative inline-block">
                                        <Brain className="w-5 h-5 text-white" />
                                        {backgroundActivity.length > 0 && (
                                            <svg
                                                className="absolute top-0 left-0 w-5 h-5 animate-spin"
                                                viewBox="0 0 20 20"
                                                fill="none"
                                                xmlns="http://www.w3.org/2000/svg"
                                                style={{ zIndex: 1 }}
                                            >
                                                <circle
                                                    cx="10"
                                                    cy="10"
                                                    r="8"
                                                    stroke="#3B82F6"
                                                    strokeWidth="3"
                                                    strokeDasharray="40 20"
                                                    strokeLinecap="round"
                                                />
                                            </svg>
                                        )}
                                    </span>
                                </div>
                            }
                        >
                            <button
                                onClick={() => navigate("/vocabulary")}
                                className="flex items-center w-full gap-2 px-4 py-3 text-sm text-gray-800 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-gray-800 transition"
                            >
                                <span className="relative inline-block">
                                    <BookText className="w-4 h-4" />
                                    {backgroundActivity.length > 0 && (
                                        <svg
                                            className="absolute top-0 left-0 w-4 h-4 animate-spin"
                                            viewBox="0 0 16 16"
                                            fill="none"
                                            xmlns="http://www.w3.org/2000/svg"
                                            style={{ zIndex: 1 }}
                                        >
                                            <circle
                                                cx="8"
                                                cy="8"
                                                r="6"
                                                stroke="#3B82F6"
                                                strokeWidth="2"
                                                strokeDasharray="20 8"
                                                strokeLinecap="round"
                                            />
                                        </svg>
                                    )}
                                </span>
                                Vocabulary
                            </button>
                            <button
                                onClick={() => navigate("/topic-memory")}
                                className="flex items-center w-full gap-2 px-4 py-3 text-sm text-gray-800 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-gray-800 transition"
                            >
                                <span className="relative inline-block">
                                    <Archive className="w-4 h-4" />
                                    {backgroundActivity.length > 0 && (
                                        <svg
                                            className="absolute top-0 left-0 w-4 h-4 animate-spin"
                                            viewBox="0 0 16 16"
                                            fill="none"
                                            xmlns="http://www.w3.org/2000/svg"
                                            style={{ zIndex: 1 }}
                                        >
                                            <circle
                                                cx="8"
                                                cy="8"
                                                r="6"
                                                stroke="#3B82F6"
                                                strokeWidth="2"
                                                strokeDasharray="20 8"
                                                strokeLinecap="round"
                                            />
                                        </svg>
                                    )}
                                </span>
                                Topic Memory
                            </button>
                            <button
                                onClick={() => navigate("/grammar-map")}
                                className="flex items-center w-full gap-2 px-4 py-3 text-sm text-gray-800 dark:text-gray-100 hover:bg-blue-50 dark:hover:bg-gray-800 transition"
                            >
                                <span className="relative inline-block">
                                    <Brain className="w-4 h-4" />
                                    {backgroundActivity.length > 0 && (
                                        <svg
                                            className="absolute top-0 left-0 w-4 h-4 animate-spin"
                                            viewBox="0 0 16 16"
                                            fill="none"
                                            xmlns="http://www.w3.org/2000/svg"
                                            style={{ zIndex: 1 }}
                                        >
                                            <circle
                                                cx="8"
                                                cy="8"
                                                r="6"
                                                stroke="#3B82F6"
                                                strokeWidth="2"
                                                strokeDasharray="20 8"
                                                strokeLinecap="round"
                                            />
                                        </svg>
                                    )}
                                </span>
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
                        {debugEnabled && (
                        <button
                            onClick={() => setShowDebugModal(true)}
                            className="flex items-center gap-3 px-4 py-3 text-sm font-semibold text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/40 dark:text-yellow-400 transition w-full text-left"
                        >
                            <span className="w-5 h-5 rounded-full bg-yellow-400 text-white flex items-center justify-center text-xs font-semibold">!</span>
                            Debug: Delete All User Data
                        </button>
                        )}
                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-3 px-4 py-3 text-sm font-semibold text-red-600 hover:bg-red-50 dark:hover:bg-red-900/40 dark:text-red-400 transition w-full text-left"
                        >
                            <LogOut className="w-4 h-4" />
                            Logout
                        </button>
                    </Dropdown>
                </div>
            </div>
            {debugEnabled && showDebugModal && (
                <Modal onClose={() => { setShowDebugModal(false); setDebugResult(null); }}>
                    {!debugResult ? (
                        <div>
                            <h2 className="text-lg font-bold mb-2 text-yellow-600">Delete All User Data</h2>
                            <p className="mb-4">Are you sure you want to delete <b>ALL</b> your user data except your name, password, and session? <br/>This cannot be undone!</p>
                            <div className="flex gap-4 justify-end">
                                <button
                                    className="px-4 py-2 rounded text-sm font-medium bg-gray-300 hover:bg-gray-400 text-gray-900"
                                    onClick={() => setShowDebugModal(false)}
                                >
                                    Cancel
                                </button>
                                <button
                                    className="px-4 py-2 rounded text-sm font-medium bg-yellow-500 hover:bg-yellow-600 text-white"
                                    onClick={async () => {
                                        try {
                                            const res = await debugDeleteUserData();
                                            if (res.status) {
                                                setDebugResult({ success: true, message: res.status });
                                            } else if (res.error) {
                                                setDebugResult({ success: false, message: res.error });
                                            } else {
                                                setDebugResult({ success: false, message: "Unknown error" });
                                            }
                                        } catch (e) {
                                            setDebugResult({ success: false, message: "Failed to delete user data" });
                                        }
                                    }}
                                >
                                    Yes, Delete All Data
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div>
                            <h2 className={`text-lg font-bold mb-2 ${debugResult.success ? "text-green-600" : "text-red-600"}`}>{debugResult.success ? "Success" : "Error"}</h2>
                            <p className="mb-4">{debugResult.message}</p>
                            <div className="flex justify-end">
                                <button
                                    className="px-4 py-2 rounded text-sm font-medium bg-blue-500 hover:bg-blue-600 text-white"
                                    onClick={() => { setShowDebugModal(false); setDebugResult(null); }}
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    )}
                </Modal>
            )}
        </header>
    );
}

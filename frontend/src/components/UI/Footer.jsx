import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
    User,
    Settings,
    Menu,
    LogOut,
    Moon,
    Sun,
    PanelTop,
    Mail,
} from "lucide-react";
import useAppStore from "../../store/useAppStore";
import { logout, sendSupportFeedback } from "../../api";
import Modal from "./Modal";
import Button from "./Button";

export default function Footer() {
    const navigate = useNavigate();
    const location = useLocation();
    const darkMode = useAppStore((state) => state.darkMode);
    const toggleDarkMode = useAppStore((state) => state.toggleDarkMode);
    const username = useAppStore((state) => state.username);
    const isAdmin = useAppStore((state) => state.isAdmin);

    const [showFeedback, setShowFeedback] = useState(false);
    const [fbMessage, setFbMessage] = useState("");
    const [fbError, setFbError] = useState("");
    const [fbSuccess, setFbSuccess] = useState("");

    const handleLogout = async () => {
        try {
            await logout();
        } catch (err) {
            console.warn("[CLIENT] Logout request failed:", err);
        }

        localStorage.removeItem("username");
        useAppStore.getState().resetStore();
        navigate("/");
    };

    const handleSendFeedback = async () => {
        if (!fbMessage.trim()) {
            setFbError("Please enter a message.");
            return;
        }
        try {
            await sendSupportFeedback(fbMessage.trim());
            setFbSuccess("Feedback sent. Thank you!");
            setFbMessage("");
            setFbError("");
        } catch (err) {
            setFbError("❌ Could not send feedback.");
        }
    };


    const isNameInputPage = location.pathname === "/" || location.pathname === "/nameinput";

    const buttonBase =
        "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition hover:bg-gray-200 dark:hover:bg-gray-700";

    const iconStyle = "w-4 h-4";

    return (
        <footer
            className={`fixed bottom-0 w-full z-50 border-t ${darkMode ? "bg-gray-900 border-gray-700 text-white" : "bg-white border-gray-200 text-gray-800"
                }`}
        >
            <div className="max-w-5xl mx-auto flex flex-wrap justify-center sm:justify-between items-center px-4 py-3 gap-3">
                {!isNameInputPage && (
                    <div className="flex flex-wrap gap-3 items-center">
                        {!isAdmin && (
                            <>
                                <button onClick={() => navigate("/profile")} className={buttonBase}>
                                    <User className={iconStyle} />
                                    Profile
                                </button>
                                <button onClick={() => navigate("/settings")} className={buttonBase}>
                                    <Settings className={iconStyle} />
                                    Settings
                                </button>
                                <button onClick={() => navigate("/menu")} className={buttonBase}>
                                  <Menu className={iconStyle} />
                                  Menu
                                </button>
                            </>
                        )}

                        {isAdmin && (
                            <>
                                <button onClick={() => navigate("/admin-panel")} className={buttonBase}>
                                    <PanelTop className={iconStyle} />
                                    Admin Panel
                                </button>
                                <button onClick={() => navigate("/menu")} className={buttonBase}>
                                    <Menu className={iconStyle} />
                                    Menu
                                </button>
                            </>
                        )}
                        <button onClick={handleLogout} className={buttonBase}>
                            <LogOut className={iconStyle} />
                            Logout
                        </button>
                    </div>
                )}

                {/* Right block: always right-aligned */}
                <div className="flex gap-2 items-center ml-auto">
                    <button onClick={toggleDarkMode} className={buttonBase}>
                        {darkMode ? <Sun className={iconStyle} /> : <Moon className={iconStyle} />}
                        {darkMode ? "Light Mode" : "Dark Mode"}
                    </button>
                    <button onClick={() => { setShowFeedback(true); setFbError(""); setFbSuccess(""); }} className={buttonBase}>
                        <Mail className={iconStyle} />
                        Support
                    </button>
                </div>
            </div>
            {showFeedback && (
                <Modal onClose={() => { setShowFeedback(false); setFbError(""); setFbSuccess(""); }}>
                    <h2 className="text-lg font-bold mb-2">Send Feedback (anonymous)</h2>
                    <textarea
                        value={fbMessage}
                        onChange={(e) => setFbMessage(e.target.value)}
                        className="w-full h-32 mb-3 p-2 rounded border dark:bg-gray-800 dark:text-white"
                    />
                    {fbError && <p className="text-red-600 text-sm mb-2">{fbError}</p>}
                    {fbSuccess && <p className="text-green-600 text-sm mb-2">{fbSuccess}</p>}
                    <div className="flex justify-end gap-2">
                        <Button variant="secondary" onClick={() => setShowFeedback(false)}>
                            Cancel
                        </Button>
                        <Button variant="primary" onClick={handleSendFeedback}>
                            Send
                        </Button>
                    </div>
                </Modal>
            )}
        </footer>
    );
}

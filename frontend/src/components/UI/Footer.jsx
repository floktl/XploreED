import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  User,
  Settings,
  Menu,
  LogOut,
  Moon,
  Sun,
  PanelTop,
} from "lucide-react";
import useAppStore from "../../store/useAppStore";
import { logout } from "../../api";

export default function Footer() {
  const navigate = useNavigate();
  const location = useLocation();
  const darkMode = useAppStore((state) => state.darkMode);
  const toggleDarkMode = useAppStore((state) => state.toggleDarkMode);
  const username = useAppStore((state) => state.username);
  const isAdmin = useAppStore((state) => state.isAdmin);

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
  
  
  const isNameInputPage = location.pathname === "/" || location.pathname === "/nameinput";

  const buttonBase =
    "flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition hover:bg-gray-200 dark:hover:bg-gray-700";

  const iconStyle = "w-4 h-4";

  return (
    <footer
      className={`fixed bottom-0 w-full z-50 border-t ${
        darkMode ? "bg-gray-900 border-gray-700 text-white" : "bg-white border-gray-200 text-gray-800"
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
                <button onClick={() => navigate("/profile")} className={buttonBase}>
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
              <button onClick={() => navigate("/admin-panel")} className={buttonBase}>
                <PanelTop className={iconStyle} />
                Admin Panel
              </button>
            )}
            <button onClick={handleLogout} className={buttonBase}>
              <LogOut className={iconStyle} />
              Logout
            </button>
          </div>
        )}

        <div>
          <button onClick={toggleDarkMode} className={buttonBase}>
            {darkMode ? <Sun className={iconStyle} /> : <Moon className={iconStyle} />}
            {darkMode ? "Light Mode" : "Dark Mode"}
          </button>
        </div>
      </div>
    </footer>
  );
}

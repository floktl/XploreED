import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import Button from "./Button";
import useAppStore from "../../store/useAppStore";

export default function Footer() {
  const navigate = useNavigate();
  const location = useLocation();
  const darkMode = useAppStore((state) => state.darkMode);
  const toggleDarkMode = useAppStore((state) => state.toggleDarkMode);
  const setUsername = useAppStore((state) => state.setUsername);
  const username = useAppStore((state) => state.username);

  const handleLogout = () => {
    localStorage.removeItem("username");
    setUsername(null);
    navigate("/");
  };

  const isNameInputPage = location.pathname === "/" || location.pathname === "/nameinput";

  return (
    <footer
      className={`fixed bottom-0 w-full py-2 px-4 flex flex-wrap justify-center gap-4 border-t ${
        darkMode ? "bg-gray-900 border-gray-700" : "bg-gray-50 border-gray-200"
      }`}
    >
      {!isNameInputPage && (
        <>
          {username !== "admin" && (
            <>
              <Button onClick={() => navigate("/profile")} type="link">
                👤 Profile
              </Button>
              <Button onClick={() => navigate("/profile")} type="link">
                ⚙️ Settings
              </Button>
            </>
          )}

          {username === "admin" && (
            <Button onClick={() => navigate("/admin-panel")} type="link">
              🛠️ Admin Panel
            </Button>
          )}

          <Button onClick={handleLogout} type="link">
            🚪 Logout
          </Button>
        </>
      )}

      <Button onClick={toggleDarkMode} type="link">
        {darkMode ? "☀️ Light Mode" : "🌙 Dark Mode"}
      </Button>
    </footer>
  );
}

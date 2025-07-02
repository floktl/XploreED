import React from "react";
import { useNavigate } from "react-router-dom";
import useAppStore from "../../store/useAppStore";

export default function Header() {
  const navigate = useNavigate();
  const username = useAppStore((state) => state.username);
  const darkMode = useAppStore((state) => state.darkMode);
  const isAdmin = useAppStore((state) => state.isAdmin);
  const avatarLetter = username ? username.charAt(0).toUpperCase() : "?";

  return (
    <header
      className={`fixed top-0 w-full z-50 shadow ${darkMode ? "bg-gray-800 text-white" : "bg-white text-gray-800"}`}
    >
      <div className="max-w-5xl mx-auto flex items-center justify-between px-4 py-3">
        <h1
          className="text-lg font-bold cursor-pointer"
          onClick={() => navigate("/menu")}
        >
          RealWorldLearn.com
        </h1>
        {!isAdmin && username && (
          <button
            onClick={() => navigate("/profile")}
            className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-semibold"
          >
            {avatarLetter}
          </button>
        )}
      </div>
    </header>
  );
}

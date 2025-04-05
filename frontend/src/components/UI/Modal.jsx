// Modal.jsx
import React from "react";
import clsx from "clsx";
import useAppStore from "../../store/useAppStore";
export default function Modal({ open, onClose, children }) {
  const darkMode = useAppStore((state) => state.darkMode);

  if (!open) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
      <div className={clsx("p-6 rounded-lg shadow-lg", darkMode ? "bg-gray-800" : "bg-white")}>
        {children}
        <button
          className="mt-4 px-4 py-2 rounded text-sm font-medium bg-red-500 text-white"
          onClick={onClose}
        >
          Close
        </button>
      </div>
    </div>
  );
}

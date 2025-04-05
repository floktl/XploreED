// Badge.jsx
import React from "react";
import clsx from "clsx";
import useAppStore from "../../store/useAppStore";

export default function Badge({ type = "default", children, className }) {
  const darkMode = useAppStore((state) => state.darkMode);
  const types = {
    default: darkMode ? "bg-gray-600 text-gray-100" : "bg-gray-200 text-gray-800",
    success: darkMode ? "bg-green-600 text-white" : "bg-green-200 text-green-800",
    error: darkMode ? "bg-red-600 text-white" : "bg-red-200 text-red-800",
  };

  return (
    <span
      className={clsx(
        "px-2 py-1 rounded-full text-xs font-medium",
        types[type],
        className
      )}
    >
      {children}
    </span>
  );
}

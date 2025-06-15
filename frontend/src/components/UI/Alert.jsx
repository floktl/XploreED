// Alert.jsx
import React from "react";
import clsx from "clsx";
import useAppStore from "../../store/useAppStore";

export default function Alert({ type = "info", children, className }) {
  const darkMode = useAppStore((state) => state.darkMode);
  const types = {
    success: darkMode ? "bg-green-700 text-green-200" : "bg-green-100 text-green-800",
    error: darkMode ? "bg-red-900/80 text-red-100 border border-red-600" : "bg-red-50 text-red-800 border border-red-300",
    info: darkMode ? "bg-blue-700 text-blue-200" : "bg-blue-100 text-blue-800",
    warning: darkMode ? "bg-yellow-700 text-yellow-200" : "bg-yellow-100 text-yellow-800",
  };

  return (
    <div className={clsx("px-4 py-3 rounded", types[type], className)}>
      {children}
    </div>
  );
}

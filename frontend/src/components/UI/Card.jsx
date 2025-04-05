// Card.jsx
import React from "react";
import clsx from "clsx";
import useAppStore from "../../store/useAppStore";

export default function Card({ children, className }) {
  const darkMode = useAppStore((state) => state.darkMode);

  return (
    <div
      className={clsx(
        "shadow-md rounded-lg p-4",
        darkMode ? "bg-gray-800 text-white" : "bg-white text-gray-800",
        className
      )}
    >
      {children}
    </div>
  );
}

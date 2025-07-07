// Card.jsx
import React from "react";
import clsx from "clsx";
import useAppStore from "../../store/useAppStore";

export default function Card({ children, className, fit = false }) {
    const darkMode = useAppStore((state) => state.darkMode);

    return (
        <div
            className={clsx(
                "shadow-md border rounded-lg p-4 backdrop-blur-sm",
                fit && "h-[calc(100vh-7rem)] overflow-y-auto",
                darkMode
                    ? "bg-gray-800 text-white border-gray-800"
                    : "bg-white/70 text-gray-800 border-gray-100",
                className
            )}
        >
            {children}
        </div>
    );
}

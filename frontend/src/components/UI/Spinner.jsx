// Spinner.jsx
import React from "react";
import useAppStore from "../../store/useAppStore";

export default function Spinner() {
    const darkMode = useAppStore((state) => state.darkMode);

    return (
        <div className="flex justify-center items-center">
            <div
                className={`animate-spin rounded-full h-6 w-6 border-2 ${darkMode ? "border-gray-600 border-t-white" : "border-gray-200 border-t-blue-500"
                    }`}
            ></div>
        </div>
    );
}

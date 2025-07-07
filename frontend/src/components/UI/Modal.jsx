// Modal.jsx
import React from "react";
import clsx from "clsx";
import useAppStore from "../../store/useAppStore";

export default function Modal({ onClose, children }) {
    const darkMode = useAppStore((state) => state.darkMode);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40 backdrop-blur-sm px-4">
            <div
                className={clsx(
                    "w-full max-w-3xl p-6 rounded-lg shadow-lg overflow-y-auto max-h-[90vh]",
                    darkMode ? "bg-gray-800 text-white" : "bg-white text-gray-800"
                )}
            >
                {children}
                <div className="flex justify-end mt-6">
                    <button
                        className="px-4 py-2 rounded text-sm font-medium bg-red-500 hover:bg-red-600 text-white"
                        onClick={onClose}
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}

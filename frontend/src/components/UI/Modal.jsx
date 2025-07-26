// Modal.jsx
import React, { useRef, useEffect } from "react";
import clsx from "clsx";
import useAppStore from "../../store/useAppStore";
import useClickOutside from "../../utils/useClickOutside";

export default function Modal({ onClose, children }) {
    const darkMode = useAppStore((state) => state.darkMode);
    const modalRef = useRef(null);
    useClickOutside(modalRef, onClose);

    // Prevent background scroll when modal is open
    useEffect(() => {
        document.body.classList.add('modal-open');
        return () => { document.body.classList.remove('modal-open'); };
    }, []);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40 backdrop-blur-sm">
            <div
                ref={modalRef}
                className={clsx(
                    "w-full max-w-3xl p-6 rounded-lg shadow-lg overflow-y-auto max-h-[90vh] mx-4",
                    darkMode ? "bg-gray-800 text-white" : "bg-white text-gray-800"
                )}
            >
                {children}
            </div>
        </div>
    );
}

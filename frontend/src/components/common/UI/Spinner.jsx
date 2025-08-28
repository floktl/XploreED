// Spinner.jsx

import useAppStore from "../../../store/useAppStore";

export default function Spinner({ size = "md" }) {
    const darkMode = useAppStore((state) => state.darkMode);

    const sizeClasses = {
        sm: "h-4 w-4",
        md: "h-6 w-6",
        lg: "h-8 w-8",
        xl: "h-12 w-12"
    };

    return (
        <div className="flex justify-center items-center">
            <div
                className={`animate-spin rounded-full border-2 ${sizeClasses[size]} ${darkMode ? "border-gray-600 border-t-white" : "border-gray-200 border-t-blue-500"
                    }`}
            ></div>
        </div>
    );
}

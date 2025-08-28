import { Play } from "lucide-react";

export default function PlayButton({
    onClick,
    loading,
    disabled,
    darkMode
}) {
    return (
        <button
            onClick={onClick}
            disabled={loading || disabled}
            className={`absolute right-14 top-1/2 transform -translate-y-1/2 rounded-full p-2
                ${darkMode
                    ? "bg-gray-600 hover:bg-gray-500"
                    : "bg-gray-200 hover:bg-gray-300"
                }
            `}
            style={{ minWidth: "36px", minHeight: "36px" }}
            title="Play sentence"
        >
            <Play className={`w-5 h-5 ${darkMode ? "text-gray-300" : "text-gray-700"}`} />
        </button>
    );
}

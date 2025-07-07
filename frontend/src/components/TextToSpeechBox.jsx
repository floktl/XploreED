import React from "react";
import { Play } from "lucide-react";
import { Input } from "./UI/UI";
import useAppStore from "../store/useAppStore";

export default function TextToSpeechBox({
    value,
    onChange,
    voiceId = "JBFqnCBsd6RMkjVDRZzb",
    modelId = "eleven_multilingual_v2",
    placeholder = "Geben Sie einen deutschen Satz ein",
    className = "",
    inputClassName = "",
    disabled = false,
}) {
    const [loading, setLoading] = React.useState(false);
    const darkMode = useAppStore((state) => state.darkMode);

    const handleSpeak = async () => {
        if (!value?.trim()) return;
        setLoading(true);
        try {
            const response = await fetch("http://localhost:5050/api/tts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text: value,
                    voice_id: voiceId,
                    model_id: modelId,
                }),
            });

            if (!response.ok) {
                const text = await response.text();
                throw new Error("Failed to fetch audio: " + text);
            }
            const audioData = await response.arrayBuffer();
            const blob = new Blob([audioData], { type: "audio/mpeg" });
            const urlObject = URL.createObjectURL(blob);

            const audio = new Audio(urlObject);
            audio.play();
        } catch (err) {
            alert("Failed to play audio: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={`flex items-center border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden bg-white dark:bg-gray-800 shadow-sm ${className}`}>
            <Input
                type="text"
                value={value}
                onChange={onChange}
                placeholder={placeholder}
                className={`flex-grow ${inputClassName}`}
                disabled={disabled}
            />
            <button
                onClick={handleSpeak}
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
                <Play className={`w-5 h-5 ${darkMode ? "text-gray-300" : "text-gray-700"
                    }`} />
            </button>
        </div>
    );
}

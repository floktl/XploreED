import { Input } from "../UI/UI";
import useAppStore from "../../../store/useAppStore";
import { playTextToSpeech } from "./Utils/ttsService";
import PlayButton from "./Components/PlayButton";

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
        try {
            setLoading(true);
            await playTextToSpeech(value, voiceId, modelId);
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
            <PlayButton
                onClick={handleSpeak}
                loading={loading}
                disabled={disabled}
                darkMode={darkMode}
            />
        </div>
    );
}

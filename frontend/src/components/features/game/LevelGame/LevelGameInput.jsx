import { Mic } from "lucide-react";
import TextToSpeechBox from "../../../common/TextToSpeechBox/TextToSpeechBox";

export default function LevelGameInput({
  typedAnswer,
  setTypedAnswer,
  isRecording,
  darkMode,
  onToggleRecording,
  elevenLabsApiKey
}) {
  return (
    <div className="relative mb-6">
      <TextToSpeechBox
        value={typedAnswer}
        onChange={e => setTypedAnswer(e.target.value)}
        placeholder="Type or speak your solution here"
        disabled={isRecording}
      />
      <button
        onClick={onToggleRecording}
        disabled={!elevenLabsApiKey || elevenLabsApiKey === "YOUR_API_KEY_HERE"}
        className={`absolute right-3 top-1/2 transform -translate-y-1/2 rounded-full p-2 ${
          isRecording
            ? "bg-red-500 animate-pulse"
            : darkMode
            ? "bg-gray-600 hover:bg-gray-500"
            : "bg-gray-200 hover:bg-gray-300"
        } transition-all`}
        title={isRecording ? "Stop recording" : "Start recording (German)"}
      >
        <Mic className={`w-5 h-5 ${
          isRecording ? "text-white" : darkMode ? "text-gray-300" : "text-gray-700"
        }`} />
      </button>
    </div>
  );
}

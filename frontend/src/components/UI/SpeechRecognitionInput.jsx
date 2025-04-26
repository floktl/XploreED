// SpeechRecognitionInput.jsx
import React, { useState, useEffect } from "react";
import { Mic, MicOff, RefreshCw } from "lucide-react";
import useAppStore from "../../store/useAppStore";

/**
 * A component that allows users to input text via speech recognition
 * 
 * @param {function} onResult - Callback function that receives the recognized text
 * @param {string} language - The language code (e.g., "de-DE" for German)
 * @param {string} placeholder - Placeholder text for the input field
 * @param {string} className - Additional CSS classes
 */
export default function SpeechRecognitionInput({
  onResult,
  language = "de-DE",
  placeholder = "Speak to input text...",
  className = ""
}) {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const [transcript, setTranscript] = useState("");
  const [recognition, setRecognition] = useState(null);
  const darkMode = useAppStore((state) => state.darkMode);

  // Initialize speech recognition
  useEffect(() => {
    // Check if speech recognition is supported
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      console.warn("Speech recognition not supported in this browser");
      setIsSupported(false);
      return;
    }

    // Create speech recognition instance
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognitionInstance = new SpeechRecognition();
    
    // Configure recognition
    recognitionInstance.continuous = false;
    recognitionInstance.interimResults = true;
    recognitionInstance.lang = language;

    // Set up event handlers
    recognitionInstance.onstart = () => {
      setIsListening(true);
    };

    recognitionInstance.onend = () => {
      setIsListening(false);
    };

    recognitionInstance.onresult = (event) => {
      const current = event.resultIndex;
      const result = event.results[current];
      const text = result[0].transcript;
      
      setTranscript(text);
      
      if (result.isFinal) {
        if (onResult) {
          onResult(text);
        }
      }
    };

    recognitionInstance.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
    };

    setRecognition(recognitionInstance);

    // Cleanup
    return () => {
      if (recognitionInstance) {
        recognitionInstance.stop();
      }
    };
  }, [language, onResult]);

  // Toggle listening
  const toggleListening = () => {
    if (!recognition) return;
    
    if (isListening) {
      recognition.stop();
    } else {
      setTranscript("");
      recognition.start();
    }
  };

  // Reset the transcript
  const resetTranscript = () => {
    setTranscript("");
    if (onResult) {
      onResult("");
    }
  };

  if (!isSupported) {
    return (
      <div className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-500"} ${className}`}>
        Speech recognition is not supported in this browser.
      </div>
    );
  }

  return (
    <div className={`flex flex-col ${className}`}>
      <div className="flex items-center">
        <input
          type="text"
          value={transcript}
          onChange={(e) => {
            setTranscript(e.target.value);
            if (onResult) {
              onResult(e.target.value);
            }
          }}
          placeholder={placeholder}
          className={`flex-grow px-4 py-2 rounded-l focus:outline-none focus:ring-2 ${
            darkMode
              ? "bg-gray-700 text-white border-gray-600 placeholder-gray-400 focus:ring-blue-500"
              : "bg-white text-gray-800 border-gray-300 placeholder-gray-500 focus:ring-blue-400"
          }`}
        />
        <button
          onClick={toggleListening}
          className={`p-2 ${
            isListening
              ? darkMode
                ? "bg-red-700 text-white"
                : "bg-red-500 text-white"
              : darkMode
              ? "bg-blue-700 text-white"
              : "bg-blue-500 text-white"
          }`}
          title={isListening ? "Stop listening" : "Start listening"}
        >
          {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
        </button>
        <button
          onClick={resetTranscript}
          className={`p-2 rounded-r ${
            darkMode
              ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
              : "bg-gray-200 text-gray-700 hover:bg-gray-300"
          }`}
          title="Reset"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>
      {isListening && (
        <div className={`text-sm mt-1 ${darkMode ? "text-blue-400" : "text-blue-600"}`}>
          Listening...
        </div>
      )}
    </div>
  );
}

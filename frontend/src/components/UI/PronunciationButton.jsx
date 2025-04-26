// PronunciationButton.jsx
import React, { useState, useEffect } from "react";
import { Volume2, VolumeX } from "lucide-react";
import useAppStore from "../../store/useAppStore";

/**
 * A button that speaks the provided text using the browser's speech synthesis API
 * 
 * @param {string} text - The text to be spoken
 * @param {string} language - The language code (e.g., "de-DE" for German)
 * @param {string} className - Additional CSS classes
 */
export default function PronunciationButton({ 
  text, 
  language = "de-DE", 
  className = "" 
}) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const [voices, setVoices] = useState([]);
  const darkMode = useAppStore((state) => state.darkMode);

  // Check if speech synthesis is supported
  useEffect(() => {
    if (!window.speechSynthesis) {
      console.warn("Speech synthesis not supported in this browser");
      setIsSupported(false);
      return;
    }

    // Load available voices
    const loadVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      setVoices(availableVoices);
    };

    // Chrome loads voices asynchronously
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    loadVoices();
  }, []);

  // Find the best German voice
  const getBestGermanVoice = () => {
    if (!voices.length) return null;

    // Try to find a German voice
    const germanVoices = voices.filter(voice => 
      voice.lang.includes('de') || voice.lang.includes('DE')
    );

    if (germanVoices.length > 0) {
      // Prefer native voices over non-native ones
      const nativeVoices = germanVoices.filter(voice => voice.localService);
      if (nativeVoices.length > 0) {
        return nativeVoices[0];
      }
      return germanVoices[0];
    }

    // If no German voice is found, return null
    return null;
  };

  const speak = () => {
    if (!window.speechSynthesis || !text) return;

    // Stop any ongoing speech
    window.speechSynthesis.cancel();

    // Create a new utterance
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language;

    // Try to use a German voice if available
    const germanVoice = getBestGermanVoice();
    if (germanVoice) {
      utterance.voice = germanVoice;
    }

    // Set event handlers
    utterance.onstart = () => setIsPlaying(true);
    utterance.onend = () => setIsPlaying(false);
    utterance.onerror = (event) => {
      console.error("Speech synthesis error:", event);
      setIsPlaying(false);
    };

    // Speak the text
    window.speechSynthesis.speak(utterance);
  };

  // Stop speaking
  const stop = () => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    setIsPlaying(false);
  };

  // Handle button click
  const handleClick = () => {
    if (isPlaying) {
      stop();
    } else {
      speak();
    }
  };

  if (!isSupported || !text) {
    return null;
  }

  return (
    <button
      onClick={handleClick}
      className={`inline-flex items-center justify-center p-2 rounded-full transition-colors ${
        darkMode 
          ? "text-blue-300 hover:bg-gray-700" 
          : "text-blue-600 hover:bg-gray-100"
      } ${className}`}
      title={isPlaying ? "Stop pronunciation" : "Listen to pronunciation"}
      aria-label={isPlaying ? "Stop pronunciation" : "Listen to pronunciation"}
    >
      {isPlaying ? (
        <VolumeX className="w-5 h-5" />
      ) : (
        <Volume2 className="w-5 h-5" />
      )}
    </button>
  );
}

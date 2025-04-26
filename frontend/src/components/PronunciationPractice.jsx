// PronunciationPractice.jsx
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Button from "./UI/Button";
import { Title, Container } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import PronunciationButton from "./UI/PronunciationButton";
import SpeechRecognitionInput from "./UI/SpeechRecognitionInput";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";

// Sample practice phrases
const PRACTICE_PHRASES = [
  {
    german: "Guten Tag",
    english: "Good day",
    difficulty: "easy"
  },
  {
    german: "Wie geht es dir?",
    english: "How are you?",
    difficulty: "easy"
  },
  {
    german: "Ich lerne Deutsch",
    english: "I am learning German",
    difficulty: "easy"
  },
  {
    german: "Das Wetter ist heute schön",
    english: "The weather is nice today",
    difficulty: "medium"
  },
  {
    german: "Können Sie mir bitte helfen?",
    english: "Can you please help me?",
    difficulty: "medium"
  },
  {
    german: "Ich möchte ein Glas Wasser, bitte",
    english: "I would like a glass of water, please",
    difficulty: "medium"
  },
  {
    german: "Die deutsche Sprache ist sehr interessant",
    english: "The German language is very interesting",
    difficulty: "hard"
  },
  {
    german: "Entschuldigung, wo ist der Bahnhof?",
    english: "Excuse me, where is the train station?",
    difficulty: "hard"
  },
  {
    german: "Ich werde morgen nach Berlin fahren",
    english: "I will travel to Berlin tomorrow",
    difficulty: "hard"
  }
];

export default function PronunciationPractice() {
  const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);
  const [userInput, setUserInput] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [difficulty, setDifficulty] = useState("easy");
  const navigate = useNavigate();
  const darkMode = useAppStore((state) => state.darkMode);
  const username = useAppStore((state) => state.username);
  const setUsername = useAppStore((state) => state.setUsername);

  // Filter phrases by difficulty
  const filteredPhrases = PRACTICE_PHRASES.filter(
    phrase => phrase.difficulty === difficulty
  );

  // Current phrase
  const currentPhrase = filteredPhrases[currentPhraseIndex];

  // Check for user session
  useEffect(() => {
    const storedUsername = localStorage.getItem("username");
    if (!username && storedUsername) {
      setUsername(storedUsername);
    }

    if (!username && !storedUsername) {
      navigate("/");
    }
  }, [username, setUsername, navigate]);

  // Handle speech recognition result
  const handleSpeechResult = (text) => {
    setUserInput(text);
  };

  // Check pronunciation
  const checkPronunciation = () => {
    if (!userInput.trim()) {
      setFeedback({
        type: "warning",
        message: "Please speak or type something first."
      });
      return;
    }

    // Simple string comparison (in a real app, you'd want more sophisticated comparison)
    const normalizedInput = userInput.toLowerCase().trim();
    const normalizedTarget = currentPhrase.german.toLowerCase().trim();

    if (normalizedInput === normalizedTarget) {
      setFeedback({
        type: "success",
        message: "Perfect pronunciation! 🎉"
      });
    } else if (normalizedInput.length > 0 && normalizedTarget.includes(normalizedInput)) {
      setFeedback({
        type: "info",
        message: "Good attempt! Try to pronounce the complete phrase."
      });
    } else {
      setFeedback({
        type: "error",
        message: "Try again. Listen carefully to the pronunciation."
      });
    }
  };

  // Move to next phrase
  const nextPhrase = () => {
    setUserInput("");
    setFeedback(null);
    
    if (currentPhraseIndex < filteredPhrases.length - 1) {
      setCurrentPhraseIndex(currentPhraseIndex + 1);
    } else {
      // Start over if we've reached the end
      setCurrentPhraseIndex(0);
    }
  };

  // Move to previous phrase
  const prevPhrase = () => {
    setUserInput("");
    setFeedback(null);
    
    if (currentPhraseIndex > 0) {
      setCurrentPhraseIndex(currentPhraseIndex - 1);
    } else {
      // Go to the last phrase if we're at the beginning
      setCurrentPhraseIndex(filteredPhrases.length - 1);
    }
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>🎤 Pronunciation Practice</Title>

        <div className="mb-6 flex justify-center">
          <div className="inline-flex rounded-md shadow-sm" role="group">
            <button
              onClick={() => setDifficulty("easy")}
              className={`px-4 py-2 text-sm font-medium rounded-l-lg ${
                difficulty === "easy"
                  ? darkMode
                    ? "bg-blue-600 text-white"
                    : "bg-blue-500 text-white"
                  : darkMode
                  ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              Easy
            </button>
            <button
              onClick={() => setDifficulty("medium")}
              className={`px-4 py-2 text-sm font-medium ${
                difficulty === "medium"
                  ? darkMode
                    ? "bg-blue-600 text-white"
                    : "bg-blue-500 text-white"
                  : darkMode
                  ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              Medium
            </button>
            <button
              onClick={() => setDifficulty("hard")}
              className={`px-4 py-2 text-sm font-medium rounded-r-lg ${
                difficulty === "hard"
                  ? darkMode
                    ? "bg-blue-600 text-white"
                    : "bg-blue-500 text-white"
                  : darkMode
                  ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              Hard
            </button>
          </div>
        </div>

        <Card className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className={`text-xl font-semibold ${darkMode ? "text-gray-100" : "text-gray-800"}`}>
              German Phrase:
            </h2>
            <PronunciationButton 
              text={currentPhrase?.german} 
              language="de-DE" 
            />
          </div>
          
          <p className={`text-2xl mb-2 ${darkMode ? "text-gray-200" : "text-gray-900"}`}>
            {currentPhrase?.german}
          </p>
          
          <p className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
            {currentPhrase?.english}
          </p>
          
          <div className="mt-6">
            <p className={`mb-2 font-medium ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
              Your pronunciation:
            </p>
            <SpeechRecognitionInput
              onResult={handleSpeechResult}
              language="de-DE"
              placeholder="Click the microphone and speak the phrase..."
              className="mb-4"
            />
            
            {feedback && (
              <Alert type={feedback.type} className="mb-4">
                {feedback.message}
              </Alert>
            )}
            
            <div className="flex flex-col sm:flex-row gap-3">
              <Button 
                variant="primary" 
                className="flex-1"
                onClick={checkPronunciation}
              >
                Check Pronunciation
              </Button>
              <Button 
                variant="secondary" 
                className="flex-1"
                onClick={nextPhrase}
              >
                Next Phrase
              </Button>
            </div>
          </div>
        </Card>
        
        <div className="flex justify-between">
          <Button 
            variant="link" 
            onClick={() => navigate("/menu")}
            className="flex items-center"
          >
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Menu
          </Button>
          
          <div className="flex gap-2">
            <Button 
              variant="ghost" 
              onClick={prevPhrase}
              className="px-3"
            >
              Previous
            </Button>
            <span className={`flex items-center ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
              {currentPhraseIndex + 1} / {filteredPhrases.length}
            </span>
            <Button 
              variant="ghost" 
              onClick={nextPhrase}
              className="px-3"
            >
              Next
            </Button>
          </div>
        </div>
      </Container>
      
      <Footer />
    </div>
  );
}

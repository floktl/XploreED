import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen, Gamepad2 } from "lucide-react";
import Button from "./UI/Button";
import { Input, Title, Container } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Spinner from "./UI/Spinner";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";
import { translateSentence } from "../api";


export default function Translator() {
  const [english, setEnglish] = useState("");
  const [german, setGerman] = useState("");
  const [feedback, setFeedback] = useState("");
  const [studentInput, setStudentInput] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showRedirectModal, setShowRedirectModal] = useState(false);

  const username = useAppStore((state) => state.username);
  const setUsername = useAppStore((state) => state.setUsername);
  const darkMode = useAppStore((state) => state.darkMode);
  const isAdmin = useAppStore((state) => state.isAdmin);
  const addMistake = useAppStore((state) => state.addMistake);
  const resetMistakes = useAppStore((state) => state.resetMistakes);
  const mistakeCount = useAppStore((state) => state.mistakeCount);
  const navigate = useNavigate();

  // Check for redirect when mistake count changes
  useEffect(() => {
    if (mistakeCount >= 3) {
      setShowRedirectModal(true);
    }
  }, [mistakeCount]);

  useEffect(() => {
    if (isAdmin) {
      navigate("/admin-panel");
      return;
    }

    const storedUsername = localStorage.getItem("username");
    if (!username && storedUsername) {
      setUsername(storedUsername);
    }

    // Redirect if no session or stored username
    if (!username && !storedUsername) {
      navigate("/");
    }
  }, [isAdmin, username, setUsername, navigate]);

  const handleTranslate = async () => {
    setError("");

    if (!english.trim() || !studentInput.trim()) {
      setError("⚠️ Please fill out both fields before submitting.");
      return;
    }

    const payload = {
      english: String(english),
      student_input: String(studentInput),
    };

    try {
      setLoading(true);
      const data = await translateSentence(payload);
      setGerman(data.german || "");
      setFeedback(data.feedback || "");

      // Check if the translation was correct
      const isCorrect = data.feedback && data.feedback.includes("✅");

      // Track mistakes and redirect if needed
      if (!isCorrect) {
        const currentMistakes = addMistake();
        console.log(`Mistake ${currentMistakes}/3`);

        if (currentMistakes >= 3) {
          setShowRedirectModal(true);
        }
      } else {
        // Reset mistakes counter on correct answer
        resetMistakes();
      }
    } catch (err) {
      console.error("[CLIENT] Translation request failed:", err);
      setError("❌ Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Handle redirection to games or dictionary
  const handleRedirect = (destination) => {
    resetMistakes();
    setShowRedirectModal(false);
    navigate(destination);
  };

  const handleReset = () => {
    setEnglish("");
    setStudentInput("");
    setGerman("");
    setFeedback("");
    setError("");
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>📝 {username ? `${username}'s` : "Your"} Translation Practice</Title>

        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            handleTranslate();
          }}
        >
          <Input
            autoFocus
            placeholder="Type your English sentence..."
            value={english}
            onChange={(e) => setEnglish(e.target.value)}
          />

          <Input
            placeholder="Your German translation"
            value={studentInput}
            onChange={(e) => setStudentInput(e.target.value)}
          />

          {error && <Alert type="warning">{error}</Alert>}
          {loading && <Spinner />}

          <div className="flex flex-col sm:flex-row gap-3 mt-2">
            <Button variant="primary" className="w-full" onClick={handleTranslate} disabled={loading}>
              🚀 {loading ? "Translating..." : "Get Feedback"}
            </Button>
            <Button variant="link" className="w-full" onClick={() => navigate("/menu")}>
              ⬅️ Back to Menu
            </Button>
          </div>
        </form>

        {german && (
          <>
            <Card className="mt-8">
              <p className={`text-lg font-semibold mb-2 ${darkMode ? "text-gray-100" : "text-blue-800"}`}>
                🗣️ Correct German:
              </p>
              <p className={`mb-3 ${darkMode ? "text-gray-200" : "text-gray-900"}`}>{german}</p>
              <div
                className={`text-sm ${darkMode ? "text-gray-300" : "text-gray-700"}`}
                dangerouslySetInnerHTML={{ __html: feedback }}
              />
            </Card>

            <div className="mt-6 text-center">
              <Button variant="secondary" onClick={handleReset}>
                🆕 New Sentence
              </Button>
            </div>
          </>
        )}
      </Container>

      <Footer />

      {/* Redirect Modal after 3 mistakes */}
      {showRedirectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`bg-${darkMode ? 'gray-800' : 'white'} p-6 rounded-lg shadow-xl max-w-md w-full`}>
            <h3 className="text-xl font-bold mb-4">Learning Suggestion</h3>
            <p className="mb-6">
              You've made 3 mistakes. It might be helpful to practice with some games or review vocabulary.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                variant="primary"
                className="flex-1"
                onClick={() => handleRedirect('/level-game')}
              >
                <Gamepad2 className="w-4 h-4 mr-2" />
                Practice with Games
              </Button>
              <Button
                variant="secondary"
                className="flex-1"
                onClick={() => handleRedirect('/vocabulary')}
              >
                <BookOpen className="w-4 h-4 mr-2" />
                Review Vocabulary
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

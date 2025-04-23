import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Menu,
  CheckCircle2,
  ArrowRightCircle,
  BookOpen,
  Gamepad2,
} from "lucide-react";
import Button from "./UI/Button";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import { Container, Title, Input } from "./UI/UI";
import { fetchLevelData, submitLevelAnswer } from "../api";
import useAppStore from "../store/useAppStore";

export default function LevelGame() {
  const [level, setLevel] = useState(0);
  const [userOrder, setUserOrder] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [typedAnswer, setTypedAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [showRedirectModal, setShowRedirectModal] = useState(false);

  const username = useAppStore((state) => state.username);
  const darkMode = useAppStore((state) => state.darkMode);
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
    const loadData = async () => {
      try {
        const data = await fetchLevelData(level);
        if (!data || !Array.isArray(data.scrambled)) {
          throw new Error("Invalid data format");
        }
        setUserOrder(data.scrambled);
        setFeedback(null);
        setTypedAnswer("");
        setSelectedIndex(null);
      } catch (err) {
        console.error("[LevelGame] Failed to load level data:", err);
        setUserOrder([]);
      }
    };

    loadData();
  }, [level]);


  const moveWord = (direction) => {
    if (selectedIndex === null) return;
    const newIndex = direction === "left" ? selectedIndex - 1 : selectedIndex + 1;
    if (newIndex < 0 || newIndex >= userOrder.length) return;

    const newOrder = [...userOrder];
    [newOrder[selectedIndex], newOrder[newIndex]] = [
      newOrder[newIndex],
      newOrder[selectedIndex],
    ];

    setUserOrder(newOrder);
    setSelectedIndex(newIndex);
  };

  const handleSubmit = async () => {
    const answer = typedAnswer.trim() || userOrder.join(" ");
    const result = await submitLevelAnswer(level, answer);
    setFeedback(result);

    // Track mistakes and redirect if needed
    if (!result.correct) {
      const currentMistakes = addMistake();
      console.log(`Mistake ${currentMistakes}/3`);

      if (currentMistakes >= 3) {
        setShowRedirectModal(true);
      }
    } else {
      // Reset mistakes counter on correct answer
      resetMistakes();
    }
  };

  // Handle redirection to games or dictionary
  const handleRedirect = (destination) => {
    resetMistakes();
    setShowRedirectModal(false);
    navigate(destination);
  };

  return (
    <div
      className={`relative min-h-screen pb-20 ${
        darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"
      }`}
    >
      <Container>
        <Title className="text-3xl font-bold mb-4">
          {username ? `${username}'s` : "Your"} Sentence Order Game
        </Title>

        <p
          className={`text-center mb-6 ${
            darkMode ? "text-gray-300" : "text-gray-600"
          }`}
        >
          Click a word, then move it left or right.
        </p>

        <div className="flex justify-center mb-6 gap-4">
          <Button variant="secondary" type="button" onClick={() => moveWord("left")}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <Button variant="secondary" type="button" onClick={() => moveWord("right")}>
            <ArrowRight className="w-5 h-5" />
          </Button>
        </div>

        <div className="flex flex-wrap justify-center gap-2 mb-4">
        {Array.isArray(userOrder) && userOrder.map((word, i) => (

            <button
              key={i}
              onClick={() => setSelectedIndex(i)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition ${
                selectedIndex === i
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-white"
              }`}
            >
              {word}
            </button>
          ))}
        </div>

        <Input
          placeholder="Or type your solution here"
          value={typedAnswer}
          onChange={(e) => setTypedAnswer(e.target.value)}
          className="mb-6"
        />

        <div className="flex flex-col sm:flex-row justify-center gap-4 mb-8">
          <Button variant="primary" type="button" onClick={handleSubmit}>
            <CheckCircle2 className="w-4 h-4 mr-2" />
            Submit
          </Button>
          <Button variant="success" type="button" onClick={() => setLevel((prev) => (prev + 1) % 10)}>
            <ArrowRightCircle className="w-4 h-4 mr-2" />
            Next
          </Button>
        </div>

        {feedback && (
          <Card className="mt-6 max-w-xl mx-auto">
            <p
              className={`text-lg font-semibold mb-2 ${
                darkMode ? "text-gray-100" : "text-blue-800"
              }`}
            >
              Correct:{" "}
              <span className="font-normal">{feedback.correct ? "Yes" : "No"}</span>
            </p>

            <div className="mb-2">
              <strong>Feedback:</strong>
              <Alert type={feedback.correct ? "success" : "error"} className="mt-1">
                <div
                  className="text-sm"
                  dangerouslySetInnerHTML={{
                    __html: feedback.feedback || "No feedback",
                  }}
                />
              </Alert>
            </div>

            <p
              className={`mt-2 text-sm ${
                darkMode ? "text-gray-400" : "text-gray-600"
              }`}
            >
              <strong>Correct Sentence:</strong> {feedback.correct_sentence}
            </p>
          </Card>
        )}

        <div className="text-center mt-8">
          <Button variant="link" type="button" onClick={() => navigate("/menu")}>
            <Menu className="w-4 h-4 mr-2" />
            Back to Menu
          </Button>
        </div>
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
                Continue Practice
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

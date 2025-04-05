import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import { Container, Title, Input } from "./UI/UI";
import { fetchLevelData, submitLevelAnswer } from "../api";
import useAppStore from "../store/useAppStore";

export default function LevelGame() {
  const [level, setLevel] = useState(0);
  const [scrambled, setScrambled] = useState([]);
  const [userOrder, setUserOrder] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [typedAnswer, setTypedAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);

  const username = useAppStore((state) => state.username) || "anonymous";
  const darkMode = useAppStore((state) => state.darkMode);
  const navigate = useNavigate();

  useEffect(() => {
    fetchLevelData(level).then((data) => {
      setScrambled(data.scrambled);
      setUserOrder(data.scrambled);
      setFeedback(null);
      setTypedAnswer("");
      setSelectedIndex(null);
    });
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
    const result = await submitLevelAnswer(level, answer, username);
    setFeedback(result);
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>🧩 Sentence Order Game</Title>
        <p className={`text-center mb-4 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>
          🧠 Click a word, then move it left or right.
        </p>

        <div className="flex justify-center mb-4 gap-3">
          <Button type="secondary" onClick={() => moveWord("left")}>⬅️</Button>
          <Button type="secondary" onClick={() => moveWord("right")}>➡️</Button>
        </div>

        <div className="flex flex-wrap justify-center gap-2 mb-4">
          {userOrder.map((word, i) => (
            <button
              key={i}
              onClick={() => setSelectedIndex(i)}
              className={`btn ${selectedIndex === i ? "bg-blue-600 text-white" : "btn-secondary"}`}
            >
              {word}
            </button>
          ))}
        </div>

        <Input
          placeholder="Or type your solution here"
          value={typedAnswer}
          onChange={(e) => setTypedAnswer(e.target.value)}
          className="mb-4"
        />

        <div className="flex flex-col sm:flex-row justify-center gap-4 mb-6">
          <Button type="primary" onClick={handleSubmit}>✅ Submit</Button>
          <Button type="success" onClick={() => setLevel((prev) => (prev + 1) % 10)}>➡️ Next</Button>
        </div>

        {feedback && (
          <Card className="mt-6 max-w-xl mx-auto">
            <p className={`text-lg font-semibold mb-2 ${darkMode ? "text-gray-100" : "text-blue-800"}`}>
              ✅ Correct:{" "}
              <span className="font-normal">{feedback.correct ? "Yes" : "No"}</span>
            </p>

            <div className="mb-2">
              <strong>📚 Feedback:</strong>
              <Alert type={feedback.correct ? "success" : "error"} className="mt-1">
                <div
                  className="text-sm"
                  dangerouslySetInnerHTML={{ __html: feedback.feedback || "No feedback" }}
                />
              </Alert>
            </div>

            <p className={`mt-2 text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
              <strong>✅ Correct Sentence:</strong> {feedback.correct_sentence}
            </p>
          </Card>
        )}

        <div className="text-center mt-6">
          <Button type="link" onClick={() => navigate("/menu")}>
            ⬅️ Back to Menu
          </Button>
        </div>
      </Container>

      <Footer />
    </div>
  );
}

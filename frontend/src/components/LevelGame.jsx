import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Menu, CheckCircle2, ArrowRightCircle } from "lucide-react";
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
  const [currentOrder, setCurrentOrder] = useState([]);
  const [typedAnswer, setTypedAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [draggedItem, setDraggedItem] = useState(null);
  const [hoverIndex, setHoverIndex] = useState(null);
  const containerRef = useRef(null);

  const username = useAppStore((state) => state.username);
  const darkMode = useAppStore((state) => state.darkMode);
  const navigate = useNavigate();

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchLevelData(level);
        if (!data || !Array.isArray(data.scrambled)) {
          throw new Error("Invalid data format");
        }
        setScrambled(data.scrambled);
        setCurrentOrder([...data.scrambled]);
        setFeedback(null);
        setTypedAnswer("");
      } catch (err) {
        console.error("[LevelGame] Failed to load level data:", err);
        setScrambled([]);
        setCurrentOrder([]);
      }
    };
  
    loadData();
  }, [level]);

  const handleDragStart = (e, index) => {
    e.dataTransfer.setData("text/plain", index);
    setDraggedItem(index);
    e.currentTarget.classList.add("dragging");
    setTimeout(() => {
      e.currentTarget.classList.add("invisible");
    }, 0);
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setHoverIndex(index);
  };

  const handleDragEnd = (e) => {
    e.currentTarget.classList.remove("dragging", "invisible");
    setDraggedItem(null);
    setHoverIndex(null);
  };

  const handleDrop = (e, dropIndex) => {
    e.preventDefault();
    const dragIndex = Number(e.dataTransfer.getData("text/plain"));
    
    if (dragIndex !== dropIndex) {
      const newOrder = [...currentOrder];
      const [removed] = newOrder.splice(dragIndex, 1);
      newOrder.splice(dropIndex, 0, removed);
      setCurrentOrder(newOrder);
    }
    setHoverIndex(null);
  };

  const handleTouchStart = (e, index) => {
    setDraggedItem(index);
    const element = e.currentTarget;
    element.classList.add("dragging");
    setTimeout(() => {
      element.classList.add("invisible");
    }, 0);
  };

  const handleTouchMove = (e) => {
    if (draggedItem === null) return;
    e.preventDefault();
    
    const touch = e.touches[0];
    const elements = document.elementsFromPoint(touch.clientX, touch.clientY);
    const wordElement = elements.find(el => el.classList.contains('word-item'));
    
    if (wordElement) {
      const index = Number(wordElement.dataset.index);
      setHoverIndex(index);
    }
  };

  const handleTouchEnd = (e) => {
    if (draggedItem === null) return;
    
    const element = document.querySelector('.word-item.dragging');
    if (element) {
      element.classList.remove("dragging", "invisible");
    }
    
    if (hoverIndex !== null && draggedItem !== hoverIndex) {
      const newOrder = [...currentOrder];
      const [removed] = newOrder.splice(draggedItem, 1);
      newOrder.splice(hoverIndex, 0, removed);
      setCurrentOrder(newOrder);
    }
    
    setDraggedItem(null);
    setHoverIndex(null);
  };

  const handleSubmit = async () => {
    try {
      const answer = typedAnswer.trim() || currentOrder.join(" ");
      const result = await submitLevelAnswer(level, answer);
      setFeedback(result);
    } catch (error) {
      console.error("Submission error:", error);
      setFeedback({
        correct: false,
        feedback: "Failed to submit answer. Please try again.",
        correct_sentence: ""
      });
    }
  };

  return (
    <div
      className={`relative min-h-screen pb-20 ${
        darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"
      }`}
      ref={containerRef}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <Container>
        <Title className="text-3xl font-bold mb-4">
          {username ? `${username}'s` : "Your"} Sentence Order Game
        </Title>

        <p className={`text-center mb-6 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>
          Drag and drop words to reorder the sentence
        </p>

        <div className="flex flex-wrap justify-center gap-2 mb-4 min-h-[60px] items-center">
          {Array.isArray(currentOrder) && currentOrder.map((word, i) => (
            <div
              key={i}
              data-index={i}
              draggable
              onDragStart={(e) => handleDragStart(e, i)}
              onDragOver={(e) => handleDragOver(e, i)}
              onDragEnd={handleDragEnd}
              onDrop={(e) => handleDrop(e, i)}
              onTouchStart={(e) => handleTouchStart(e, i)}
              className={`word-item px-4 py-2 rounded-lg text-base font-medium transition-all duration-200 ${
                draggedItem === i 
                  ? "bg-blue-600 text-white shadow-lg z-10" 
                  : hoverIndex === i 
                    ? "bg-blue-400 text-white" 
                    : darkMode 
                      ? "bg-gray-700 hover:bg-gray-600 text-white" 
                      : "bg-gray-200 hover:bg-gray-300 text-gray-800"
              } cursor-ew-resize select-none flex items-center justify-center`}
              style={{ height: "42px" }}
            >
              {word}
            </div>
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
            <p className={`text-lg font-semibold mb-2 ${darkMode ? "text-gray-100" : "text-blue-800"}`}>
              Correct: <span className="font-normal">{feedback.correct ? "Yes" : "No"}</span>
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
            <p className={`mt-2 text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
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
    </div>
  );
}
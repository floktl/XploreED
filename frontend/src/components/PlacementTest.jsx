import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchLevelData, submitLevelAnswer, setUserLevel } from "../api";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";

export default function PlacementTest({ onComplete }) {
  const [index, setIndex] = useState(0);
  const [scrambled, setScrambled] = useState([]);
  const [sentence, setSentence] = useState("");
  const [answer, setAnswer] = useState("");
  const [correct, setCorrect] = useState(0);
  const navigate = useNavigate();
  const darkMode = useAppStore((s) => s.darkMode);
  const setCurrentLevel = useAppStore((s) => s.setCurrentLevel);

  useEffect(() => {
    const load = async () => {
      const data = await fetchLevelData(index);
      setScrambled(data.scrambled || []);
      setSentence(data.sentence || "");
      setAnswer("");
    };
    load();
  }, [index]);

  const handleNext = async () => {
    const result = await submitLevelAnswer(index, answer.trim(), sentence);
    if (result.correct) setCorrect((c) => c + 1);

    if (index < 9) {
      setIndex(index + 1);
    } else {
      const finalScore = correct + (result.correct ? 1 : 0);
      await setUserLevel(finalScore);
      setCurrentLevel(finalScore);
      if (onComplete) {
        onComplete(finalScore);
      } else {
        navigate("/menu");
      }
    }
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>\n      <Container>
        <Title className="text-3xl font-bold mb-4">Placement Test</Title>
        <Card className="mb-6 p-4">
          <p className="mb-2">Question {index + 1} of 10</p>
          <p className="mb-4">Arrange the words into a correct sentence:</p>
          <div className="mb-4 font-mono">{scrambled.join(" ")}</div>
          <Input
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type your answer"
          />
        </Card>
        <div className="flex gap-4 justify-end max-w-xl mx-auto">
          <Button variant="primary" type="button" onClick={handleNext}>Next</Button>
        </div>
      </Container>
      <Footer />
    </div>
  );
}

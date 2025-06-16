import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchLevelData, submitLevelAnswer, setUserLevel } from "../api";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";

export default function PlacementTest() {
  const [index, setIndex] = useState(0);
  const [scrambled, setScrambled] = useState([]);
  const [sentence, setSentence] = useState("");
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
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
      setFeedback(null);
    };
    load();
  }, [index]);

  const handleSubmit = async () => {
    const result = await submitLevelAnswer(index, answer.trim(), sentence);
    setFeedback(result);
    if (result.correct) setCorrect((c) => c + 1);
  };

  const handleNext = async () => {
    if (index < 9) {
      setIndex(index + 1);
    } else {
      await setUserLevel(correct);
      setCurrentLevel(correct);
      navigate("/menu");
    }
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>\n      <Container>
        <Title className="text-3xl font-bold mb-4">Placement Test</Title>
        <Card className="mb-6 p-4">
          <p className="mb-2">Question {index + 1} of 10</p>
          <p className="mb-4">Arrange the words into a correct sentence:</p>
          <div className="mb-4 font-mono">{scrambled.join(" ")}</div>
          <Input value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder="Type your answer" />
          {feedback && (
            <Alert type={feedback.correct ? "success" : "error"} className="mt-4">
              <div dangerouslySetInnerHTML={{ __html: feedback.feedback }} />
            </Alert>
          )}
        </Card>
        <div className="flex gap-4 justify-end max-w-xl mx-auto">
          <Button variant="primary" type="button" onClick={handleSubmit}>Submit</Button>
          <Button variant="ghost" type="button" onClick={handleNext}>Next</Button>
        </div>
      </Container>
      <Footer />
    </div>
  );
}

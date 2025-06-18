import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  submitLevelAnswer,
  setUserLevel,
  generateAiFeedback,
} from "../api";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";
import PlacementFeedback from "./PlacementFeedback";

const SENTENCES = [
  "Ich bin Anna.",
  "Wir gehen heute einkaufen.",
  "Kannst du mir bitte helfen?",
  "Gestern habe ich einen interessanten Film gesehen.",
  "Obwohl es regnete, gingen wir spazieren.",
  "Wenn ich mehr Zeit hätte, würde ich ein Buch schreiben.",
  "Trotz seiner Müdigkeit arbeitete er bis spät in die Nacht.",
  "Hätte ich doch früher Deutsch gelernt!",
  "Der Politiker betonte, dass nachhaltige Energie entscheidend sei.",
  "Angesichts der aktuellen Lage wäre ein rasches Handeln der Regierung unerlässlich.",
];

function scramble(sentence) {
  return sentence.split(" ").sort(() => Math.random() - 0.5);
}

export default function PlacementTest({ onComplete }) {
  const [index, setIndex] = useState(0);
  const [scrambled, setScrambled] = useState([]);
  const [sentence, setSentence] = useState("");
  const [answer, setAnswer] = useState("");
  const [correct, setCorrect] = useState(0);
  const [answers, setAnswers] = useState({});
  const [feedbackText, setFeedbackText] = useState("");
  const [feedbackSummary, setFeedbackSummary] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [finalScore, setFinalScore] = useState(0);
  const navigate = useNavigate();
  const darkMode = useAppStore((s) => s.darkMode);
  const setCurrentLevel = useAppStore((s) => s.setCurrentLevel);

  useEffect(() => {
    const s = SENTENCES[index];
    setSentence(s);
    setScrambled(scramble(s));
    setAnswer("");
  }, [index]);

  const handleNext = async () => {
    const res = await submitLevelAnswer(index, answer.trim(), sentence);
    if (res.correct) setCorrect((c) => c + 1);
    const id = `ex${index + 1}`;
    setAnswers((a) => ({ ...a, [id]: answer.trim() }));
    if (index < 9) {
      setIndex(index + 1);
    } else {
      const score = correct + (res.correct ? 1 : 0);
      const finalAnswers = { ...answers, [id]: answer.trim() };
      const exerciseBlock = {
        exercises: SENTENCES.map((s, i) => ({
          id: `ex${i + 1}`,
          question: s,
        })),
      };

      try {
        const fb = await generateAiFeedback({ answers: finalAnswers, exercise_block: exerciseBlock });
        setFeedbackText(fb.feedbackPrompt || "");
        setFeedbackSummary(fb.summary || null);
      } catch (e) {
        console.error("[PlacementTest] AI feedback failed", e);
      }

      await setUserLevel(score);
      setCurrentLevel(score);
      setFinalScore(score);
      setShowFeedback(true);
    }
  };

  return (
    <>
      {showFeedback ? (
        <PlacementFeedback
          feedback={feedbackText}
          summary={feedbackSummary}
          onDone={() => {
            if (onComplete) {
              onComplete(finalScore);
            } else {
              navigate("/menu");
            }
          }}
        />
      ) : (
        <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
          <Container>
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
      )}
    </>
  );
}

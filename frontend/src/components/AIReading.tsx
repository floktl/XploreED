import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Footer from "./UI/Footer";
import Spinner from "./UI/Spinner";
import useAppStore from "../store/useAppStore";
import { getReadingExercise, submitReadingAnswers } from "../api";

interface Question {
  id: string;
  question: string;
  options: string[];
  correctAnswer?: string;
}

interface ReadingData {
  text: string;
  questions: Question[];
  feedbackPrompt?: string;
  vocabHelp?: { word: string; meaning: string }[];
}

export default function AIReading() {
  const [style, setStyle] = useState<string>("story");
  const [data, setData] = useState<ReadingData | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const darkMode = useAppStore((s) => s.darkMode);

  const startExercise = async () => {
    setLoading(true);
    try {
      const d = await getReadingExercise(style);
      setData(d);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (id: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [id]: value }));
  };

  const handleSubmit = async () => {
    if (!data) return;
    setLoading(true);
    setSubmitted(true);
    try {
      const result = await submitReadingAnswers(answers, data);
      if (result?.feedbackPrompt) {
        setData({ ...data, feedbackPrompt: result.feedbackPrompt });
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  if (!data) {
    return (
      <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
        <Container>
          <Title>📖 AI Reading Exercise</Title>
          <Card className="space-y-4">
            <label className="block font-medium">Choose a text type:</label>
            <select value={style} onChange={(e) => setStyle(e.target.value)} className="border p-2 rounded-md">
              <option value="story">Story</option>
              <option value="letter">Letter</option>
              <option value="news">News</option>
            </select>
            <Button onClick={startExercise} variant="primary">Start</Button>
            {loading && <Spinner />}
          </Card>
          <div className="mt-6 text-center">
            <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")}>🔙 Back to Menu</Button>
          </div>
        </Container>
        <Footer />
      </div>
    );
  }

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>📖 Reading Exercise</Title>
        <Card className="space-y-4">
          <p>{data.text}</p>
          {data.questions.map((q) => (
            <div key={q.id} className="space-y-2">
              <p className="font-medium">{q.question}</p>
              {q.options.map((opt) => (
                <Button key={opt} type="button" variant={answers[q.id] === opt ? "primary" : "secondary"} onClick={() => handleSelect(q.id, opt)} disabled={submitted}>
                  {opt}
                </Button>
              ))}
            </div>
          ))}
          {!submitted && <Button onClick={handleSubmit} variant="success">Submit Answers</Button>}
          {submitted && data.feedbackPrompt && <div dangerouslySetInnerHTML={{ __html: data.feedbackPrompt }} />}
        </Card>
        <div className="mt-6 text-center">
          <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")}>🔙 Back to Menu</Button>
        </div>
      </Container>
      <Footer />
    </div>
  );
}

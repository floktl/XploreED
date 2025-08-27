import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Card from "../components/UI/Card";
import Spinner from "../components/UI/Spinner";
import useAppStore from "../store/useAppStore";
import { getProgressTest, submitProgressTest } from "../api";
import {
  LevelUpTestResult,
  LevelUpTestStages
} from "../components/LevelUpTest";

export default function LevelUpTestView() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [stage, setStage] = useState(0);
  const [aiPassed, setAiPassed] = useState(false);
  const [orderAnswer, setOrderAnswer] = useState("");
  const [translation, setTranslation] = useState("");
  const [readingAns, setReadingAns] = useState({});
  const [result, setResult] = useState(null);
  const [actions, setActions] = useState(null);
  const navigate = useNavigate();
  const darkMode = useAppStore((s) => s.darkMode);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const d = await getProgressTest();
        setData(d);
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSubmit = async () => {
    if (!data) return;
    setLoading(true);
    try {
      const payload = {
        sentence: data.sentence,
        english: data.english,
        reading: data.reading,
        answers: {
          ai_pass: aiPassed,
          order: orderAnswer,
          translation: translation,
          reading: readingAns,
        },
      };
      const res = await submitProgressTest(payload);
      setResult(res.passed);
    } catch {
      setResult(false);
    } finally {
      setLoading(false);
    }
  };

  const handleStageComplete = (stageIndex) => {
    if (stageIndex === 0) {
      setAiPassed(true);
      setStage(1);
    }
  };

  const handleNextStage = (nextStage) => {
    setStage(nextStage);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card>Failed to load test.</Card>
      </div>
    );
  }

  if (result !== null) {
    return (
      <LevelUpTestResult
        result={result}
        onNavigate={navigate}
        darkMode={darkMode}
      />
    );
  }

  return (
    <LevelUpTestStages
      stage={stage}
      data={data}
      orderAnswer={orderAnswer}
      setOrderAnswer={setOrderAnswer}
      translation={translation}
      setTranslation={setTranslation}
      readingAns={readingAns}
      setReadingAns={setReadingAns}
      onStageComplete={handleStageComplete}
      onNextStage={handleNextStage}
      onSubmit={handleSubmit}
      actions={actions}
      darkMode={darkMode}
    />
  );
}

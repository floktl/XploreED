import React, { useEffect, useState } from "react";
import Card from "./UI/Card";
import Button from "./UI/Button";
import { Input } from "./UI/UI";
import {
  getAiExercises,
  saveVocabWords,
  submitExerciseAnswers,
  argueExerciseAnswers,
} from "../api";

export default function AIExerciseBlock({ data, blockId = "ai", completed = false, onComplete, mode = "student", fetchExercisesFn = getAiExercises }) {
  const [current, setCurrent] = useState(data || null);
  const [loadingInit, setLoadingInit] = useState(
    mode === "student" && (!data || !Array.isArray(data.exercises))
  );
  const [isComplete, setIsComplete] = useState(completed);
  const [stage, setStage] = useState(1);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [evaluation, setEvaluation] = useState({});
  const [passed, setPassed] = useState(false);
  const [arguing, setArguing] = useState(false);


  const exercises = current?.exercises || [];
  const instructions = current?.instructions;
  const feedbackPrompt = current?.feedbackPrompt;

  useEffect(() => {
    setIsComplete(completed);
  }, [completed]);

  useEffect(() => {
    if (mode !== "student") return;
    if (!current || !Array.isArray(current.exercises)) {
      setLoadingInit(true);
      fetchExercisesFn()
        .then((d) => setCurrent(d))
        .catch(() => setCurrent(null))
        .finally(() => setLoadingInit(false));
    }
  }, [mode, fetchExercisesFn]);

  useEffect(() => {
    if (mode === "student" && submitted && passed && !isComplete) {
      setIsComplete(true);
      onComplete?.();
    }
  }, [submitted, passed, isComplete, onComplete, mode]);

  if (mode !== "student") {
    return (
      <Card className="text-center py-4">
        <p>🤖 AI Exercise</p>
      </Card>
    );
  }

  if (loadingInit) {
    return (
      <Card className="text-center py-4">
        <p>Loading personalized AI exercises...</p>
      </Card>
    );
  }

  if (!current || !Array.isArray(current.exercises)) {
    return (
      <Card className="bg-red-100 text-red-800">
        <p>Failed to load AI exercise.</p>
      </Card>
    );
  }


  const handleSelect = (exId, value) => {
    setAnswers((prev) => ({ ...prev, [exId]: value }));
  };

  const handleSubmit = async () => {
    setSubmitted(true);
    try {
      const result = await submitExerciseAnswers(blockId, answers, current);
      if (result?.results) {
        const map = {};
        result.results.forEach((r) => {
          map[r.id] = r.correct_answer;
        });
        setEvaluation(map);
      }
      if (result?.feedbackPrompt) {
        setCurrent((prev) => ({ ...prev, feedbackPrompt: result.feedbackPrompt }));
      }
      if (result?.pass) {
        setPassed(true);
        if (mode === "student" && Array.isArray(result.results)) {
          const words = result.results.map((r) => r.correct_answer);
          await saveVocabWords(words);
        }
      }
    } catch (e) {
      console.error("Submission failed:", e);
    }
  };

  const handleArgue = async () => {
    setArguing(true);
    try {
      const result = await argueExerciseAnswers(blockId, answers, current);
      if (result?.results) {
        const map = {};
        result.results.forEach((r) => {
          map[r.id] = r.correct_answer;
        });
        setEvaluation(map);
      }
      if (result?.pass) {
        setPassed(true);
      }
    } catch (err) {
      console.error("Argue failed:", err);
    } finally {
      setArguing(false);
    }
  };

  const handleNext = async () => {
    if (passed) return;
    setLoading(true);
    try {
      const newData = await fetchExercisesFn({ answers });
      setCurrent(newData);
      setStage((s) => s + 1);
      setAnswers({});
      setSubmitted(false);
      setEvaluation({});
      setPassed(false);
      setArguing(false);
    } catch (err) {
      alert("Failed to load AI exercises");
    } finally {
      setLoading(false);
    }
  };

  const showVocab = stage > 1 && Array.isArray(current.vocabHelp);

  return (
    <Card className="space-y-4">
      {stage === 1 && current.title && (
        <h3 className="text-xl font-semibold">{current.title}</h3>
      )}
      {instructions && <p>{instructions}</p>}
      <div className="space-y-6">
        {exercises.map((ex) => (
          <div key={ex.id} className="mb-4">
            {ex.type === "gap-fill" ? (
              <>
                <div className="mb-2 font-medium">
                  {(() => {
                    const parts = String(ex.question).split("___");
                    return (
                      <>
                        {parts[0]}
                        {answers[ex.id] ? (
                          <span className="text-blue-600">{answers[ex.id]}</span>
                        ) : (
                          <span className="text-gray-400">___</span>
                        )}
                        {parts[1]}
                      </>
                    );
                  })()}
                </div>
                <div className="flex flex-wrap gap-2">
                  {ex.options.map((opt) => (
                    <Button
                      key={opt}
                      variant={answers[ex.id] === opt ? "primary" : "secondary"}
                      type="button"
                      onClick={() => handleSelect(ex.id, opt)}
                      disabled={submitted}
                    >
                      {opt}
                    </Button>
                  ))}
                </div>
              </>
            ) : (
              <>
            <label className="block mb-2 font-medium">{ex.question}</label>
            <Input
              type="text"
              value={answers[ex.id] || ""}
              onChange={(e) => handleSelect(ex.id, e.target.value)}
              disabled={submitted}
              placeholder="Your answer"
            />
              </>
            )}
            {submitted && (
              <div className="mt-2">
                {String(answers[ex.id]).trim().toLowerCase() ===
                String(evaluation[ex.id]).trim().toLowerCase() ? (
                  <span className="text-green-600">✅ Correct!</span>
                ) : (
                  <span className="text-red-600">
                    ❌ Incorrect. Correct answer: <b>{evaluation[ex.id]}</b>
                  </span>
                )}
                <div className="text-xs text-gray-500 mt-1">{ex.explanation}</div>
              </div>
            )}
          </div>
        ))}
        {!submitted && (
          <Button type="button" variant="success" onClick={handleSubmit}>
            Submit Answers
          </Button>
        )}
        {submitted && feedbackPrompt && (
          <div className="mt-4 italic text-blue-700 dark:text-blue-300">
            {feedbackPrompt}
          </div>
        )}
        {submitted && !passed && (
          <div className="mt-4 flex gap-2">
            <Button
              type="button"
              variant="danger"
              onClick={handleArgue}
              disabled={arguing}
            >
              {arguing ? "Thinking..." : "Argue with AI"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={handleNext}
              disabled={loading || arguing}
            >
              {loading ? "Loading..." : arguing ? "Thinking..." : "Continue"}
            </Button>
          </div>
        )}
        {submitted && passed && (
          <div className="mt-4 text-green-700">All exercises correct!</div>
        )}
      </div>
      {showVocab && current.vocabHelp && current.vocabHelp.length > 0 && (
        <div className="mt-4">
          <strong>Vocabulary Help:</strong>
          <ul className="list-disc ml-6">
            {current.vocabHelp.map((v, idx) => (
              <li key={v.word || idx}>
                <span className="font-medium">{v.word}</span>: {v.meaning}
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}

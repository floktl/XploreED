import React, { useState, useEffect } from "react";
import Card from "./UI/Card";
import Button from "./UI/Button";
import { getAiExercises } from "../api";

export default function AIExerciseBlock({ data }) {
  const [current, setCurrent] = useState(data);
  const [loadingInit, setLoadingInit] = useState(!data || !Array.isArray(data.exercises));

  useEffect(() => {
    if (!current || !Array.isArray(current.exercises)) {
      setLoadingInit(true);
      getAiExercises()
        .then((d) => setCurrent(d))
        .catch(() => setCurrent(null))
        .finally(() => setLoadingInit(false));
    }
  }, []);

  if (loadingInit) {
    return (
      <Card className="text-center py-4">
        <p>Loading AI exercises...</p>
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
  const [current, setCurrent] = useState(data);
  const [stage, setStage] = useState(1);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const exercises = current.exercises || [];
  const instructions = current.instructions;
  const feedbackPrompt = current.feedbackPrompt;

  const handleSelect = (exId, value) => {
    setAnswers((prev) => ({ ...prev, [exId]: value }));
  };

  const handleSubmit = () => {
    setSubmitted(true);
  };

  const allCorrect = exercises.every(
    (ex) =>
      String(answers[ex.id]).trim().toLowerCase() ===
      String(ex.correctAnswer).trim().toLowerCase()
  );

  const handleNext = async () => {
    if (allCorrect) return;
    setLoading(true);
    try {
      const newData = await getAiExercises();
      setCurrent(newData);
      setStage((s) => s + 1);
      setAnswers({});
      setSubmitted(false);
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
                <input
                  type="text"
                  className="border rounded p-2 w-full"
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
                String(ex.correctAnswer).trim().toLowerCase() ? (
                  <span className="text-green-600">✅ Correct!</span>
                ) : (
                  <span className="text-red-600">
                    ❌ Incorrect. Correct answer: <b>{ex.correctAnswer}</b>
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
        {submitted && !allCorrect && (
          <div className="mt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={handleNext}
              disabled={loading}
            >
              {loading ? "Loading..." : "Continue"}
            </Button>
          </div>
        )}
        {submitted && allCorrect && (
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

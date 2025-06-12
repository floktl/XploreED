import React, { useState } from "react";
import Button from "./UI/Button";

export default function AIExerciseBlock({ data }) {
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);

  if (!data || !Array.isArray(data.exercises)) return null;

  const handleSelect = (exId, option) => {
    setAnswers((prev) => ({ ...prev, [exId]: option }));
  };

  const handleSubmit = () => {
    setSubmitted(true);
  };

  return (
    <div className="space-y-4">
      {data.instructions && <p>{data.instructions}</p>}
      {data.type === "gap-fill" && (
        <div className="space-y-6">
          {data.exercises.map((ex) => (
            <div key={ex.id} className="mb-4">
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
              {submitted && (
                <div className="mt-2">
                  {answers[ex.id] === ex.correctAnswer ? (
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
          {submitted && data.feedbackPrompt && (
            <div className="mt-4 italic text-blue-700 dark:text-blue-300">
              {data.feedbackPrompt}
            </div>
          )}
        </div>
      )}
      {data.vocabHelp && data.vocabHelp.length > 0 && (
        <div className="mt-4">
          <strong>Vocabulary Help:</strong>
          <ul className="list-disc ml-6">
            {data.vocabHelp.map((v, idx) => (
              <li key={v.word || idx}>
                <span className="font-medium">{v.word}</span>: {v.meaning}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

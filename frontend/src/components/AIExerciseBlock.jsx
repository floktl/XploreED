import React, { useState } from "react";
import Card from "./UI/Card";
import Button from "./UI/Button";

export default function AIExerciseBlock({ data }) {
  if (!data || !Array.isArray(data.exercises)) {
    return (
      <Card className="bg-red-100 text-red-800">
        <p>Invalid AI exercise data.</p>
      </Card>
    );
  }

  const [stage, setStage] = useState(1);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);

  const exercises = stage === 1 ? data.exercises : data.nextExercises || [];
  const instructions = stage === 1 ? data.instructions : data.nextInstructions;
  const feedbackPrompt = stage === 1 ? data.feedbackPrompt : data.nextFeedbackPrompt;

  const handleSelect = (exId, value) => {
    setAnswers((prev) => ({ ...prev, [exId]: value }));
  };

  const handleSubmit = () => {
    setSubmitted(true);
  };

  const handleNext = () => {
    setStage(2);
    setAnswers({});
    setSubmitted(false);
  };

  const showVocab = (stage === 2 || !data.nextExercises) && Array.isArray(data.vocabHelp);

  return (
    <Card className="space-y-4">
      {stage === 1 && data.title && <h3 className="text-xl font-semibold">{data.title}</h3>}
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
        {submitted && stage === 1 && data.nextExercises && (
          <div className="mt-4">
            <Button type="button" variant="secondary" onClick={handleNext}>
              Continue
            </Button>
          </div>
        )}
      </div>
      {showVocab && data.vocabHelp && data.vocabHelp.length > 0 && (
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
    </Card>
  );
}

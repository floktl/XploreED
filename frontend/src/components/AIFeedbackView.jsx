import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import useAppStore from "../store/useAppStore";
import Card from "./UI/Card";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";

export default function AIFeedbackView() {
  const { feedbackId } = useParams();
  const [feedback, setFeedback] = useState(null);
  const [error, setError] = useState("");
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const navigate = useNavigate();
  const isAdmin = useAppStore((state) => state.isAdmin);

  useEffect(() => {
    if (isAdmin) {
      navigate("/admin-panel");
      return;
    }

    // Fetch feedback from localStorage (mocked)
    const allFeedback = JSON.parse(localStorage.getItem("aiFeedback") || "[]");
    const item = allFeedback.find(fb => String(fb.id) === String(feedbackId));
    if (!item) setError("Could not load feedback.");
    setFeedback(item);
  }, [feedbackId, isAdmin, navigate]);

  const handleSelect = (exId, option) => {
    setAnswers(prev => ({ ...prev, [exId]: option }));
  };

  const handleSubmit = () => {
    setSubmitted(true);
  };

  return (
    <div className="min-h-screen pb-20 bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white">
      <Container>
        <Title>🤖 AI Feedback {feedbackId}</Title>
        {error && <p className="text-red-500">{error}</p>}
        {!feedback ? (
          <p>Loading...</p>
        ) : (
          <Card>
            <h3 className="text-xl font-semibold">{feedback.title}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Added on {new Date(feedback.created_at).toLocaleString()}
            </p>
            {feedback.instructions && (
              <div className="mt-4">
                <strong>Instructions:</strong> {feedback.instructions}
              </div>
            )}
            {feedback.type === "gap-fill" && feedback.exercises && (
              <div className="mt-4 space-y-6">
                {feedback.exercises.map((ex, idx) => (
                  <div key={ex.id} className="mb-4">
                   <div className="mb-2 font-medium">
                      {(() => {
                        const parts = String(ex.question).split("___");
                        return (
                          <>
                            {parts[0]}
                            {answers[ex.id]
                              ? <span className="text-blue-600">{answers[ex.id]}</span>
                              : <span className="text-gray-400">___</span>
                            }
                            {parts[1]}
                          </>
                        );
                      })()}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {ex.options.map(opt => (
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
                {submitted && feedback.feedbackPrompt && (
                  <div className="mt-4 italic text-blue-700 dark:text-blue-300">
                    {feedback.feedbackPrompt}
                  </div>
                )}
              </div>
            )}
            {feedback.vocabHelp && feedback.vocabHelp.length > 0 && (
              <div className="mt-4">
                <strong>Vocabulary Help:</strong>
                <ul className="list-disc ml-6">
                  {feedback.vocabHelp.map((v, idx) => (
                    <li key={v.word || idx}>
                      <span className="font-medium">{v.word}</span>: {v.meaning}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Card>
        )}
        <div className="text-center mt-8">
          <Button
            variant="link"
            type="button"
            onClick={() => navigate("/ai-feedback")}
          >
            ⬅ Back to AI Feedback
          </Button>
        </div>
      </Container>
    </div>
  );
}
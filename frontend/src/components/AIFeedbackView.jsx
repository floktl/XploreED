import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import useAppStore from "../store/useAppStore";
import Card from "./UI/Card";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";
import { getAiFeedbackItem, generateAiFeedback } from "../api";

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

    const fetchData = async () => {
      try {
        const item = await getAiFeedbackItem(feedbackId);
        setFeedback(item);
      } catch (err) {
        setError("Could not load feedback.");
      }
    };

    fetchData();
  }, [feedbackId, isAdmin, navigate]);

  const handleSelect = (exId, option) => {
    setAnswers(prev => ({ ...prev, [exId]: option }));
  };

  const handleSubmit = async () => {
    try {
      const result = await generateAiFeedback({ answers, feedbackId });
      if (result && result.feedbackPrompt) {
        setFeedback((prev) => ({ ...prev, feedbackPrompt: result.feedbackPrompt }));
      }
      if (result && Array.isArray(result.results)) {
        const map = {};
        result.results.forEach((r) => {
          map[r.id] = r.correct_answer;
        });
        setFeedback((prev) => ({
          ...prev,
          exercises: Array.isArray(prev?.exercises)
            ? prev.exercises.map((ex) => ({
                ...ex,
                correctAnswer: map[ex.id],
              }))
            : prev?.exercises,
        }));
      }
    } catch (err) {
      console.error("Failed to generate AI feedback", err);
    } finally {
      setSubmitted(true);
    }
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
            {feedback.exercises && (
              <div className="mt-4 space-y-6">
                {feedback.exercises.map((ex) => (
                  <div key={ex.id} className="mb-4">
                    {ex.type === "gap-fill" ? (
                      <>
                        <div className="mb-2 font-medium">
                          {String(ex.question)
                            .split("___")
                            .map((part, idx, arr) => (
                              <React.Fragment key={idx}>
                                {part}
                                {idx < arr.length - 1 && (
                                  answers[ex.id] ? (
                                    <span className="text-blue-600">{answers[ex.id]}</span>
                                  ) : (
                                    <span className="text-gray-400">___</span>
                                  )
                                )}
                              </React.Fragment>
                            ))}
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
                        String(ex.correctAnswer || "").trim().toLowerCase() ? (
                          <span className="text-green-600">✅ Correct!</span>
                        ) : (
                          <span className="text-red-600">
                            ❌ Incorrect{ex.correctAnswer ? (
                              <>. Correct answer: <b>{ex.correctAnswer}</b></>
                            ) : null}
                          </span>
                        )}
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

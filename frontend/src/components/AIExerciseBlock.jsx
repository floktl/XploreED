import React, { useEffect, useState } from "react";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Spinner from "./UI/Spinner";
import { Input } from "./UI/UI";
import {
  getAiExercises,
  saveVocabWords,
  submitExerciseAnswers,
  argueExerciseAnswers,
} from "../api";
import diffWords from "../utils/diffWords";

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
  const [submitting, setSubmitting] = useState(false);
  const [nextExercise, setNextExercise] = useState(null);
  const [loadingNext, setLoadingNext] = useState(false);

  const fetchNext = async (payload = {}) => {
    setLoadingNext(true);
    try {
      const next = await fetchExercisesFn(payload);
      setNextExercise(next);
    } catch (err) {
      console.error("Failed to prefetch AI exercises", err);
      setNextExercise(null);
    } finally {
      setLoadingNext(false);
    }
  };


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
      .then((d) => {
        if (!d || !Array.isArray(d.exercises)) {
          throw new Error("Mistral API returned null or invalid exercises.");
        }
        setCurrent(d);
        fetchNext();
      })
      .catch((err) => {
        console.error("Mistral API error:", err);
        setCurrent("API_ERROR_500"); // sentinel value
      })
      .finally(() => setLoadingInit(false));
  } else {
    fetchNext();
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

 if (current === "API_ERROR_500") {
  return (
    <Card className="bg-red-100 text-red-800">
      <p>🚨 500: Mistral API Error. Please try again later.</p>
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
    setSubmitting(true);
    setSubmitted(true);
    try {
      const result = await submitExerciseAnswers(blockId, answers, current);
      if (result?.results) {
        const map = {};
        result.results.forEach((r) => {
          map[r.id] = {
            correct: r.correct_answer,
            alternatives:
              r.alternatives ||
              r.other_solutions ||
              r.other_answers ||
              []
          };
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
    } finally {
      setSubmitting(false);
      if (mode === "student") {
        fetchNext({ answers });
      }
    }
  };

  const handleArgue = async () => {
    setArguing(true);
    try {
      const result = await argueExerciseAnswers(blockId, answers, current);
      if (result?.results) {
        const map = {};
        result.results.forEach((r) => {
          map[r.id] = {
            correct: r.correct_answer,
            alternatives:
              r.alternatives ||
              r.other_solutions ||
              r.other_answers ||
              []
          };
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

  const handleNext = async (force = false) => {
    if (passed && !force) return;
    if (nextExercise) {
      setCurrent(nextExercise);
      setNextExercise(null);
      setStage((s) => s + 1);
      setAnswers({});
      setSubmitted(false);
      setEvaluation({});
      setPassed(false);
      setArguing(false);
      fetchNext();
    } else {
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
        fetchNext();
      }
    }
  };

  const showVocab = stage > 1 && Array.isArray(current.vocabHelp);

  return (
    <Card className="space-y-4">
      {stage === 1 && current.title && (
        <h3 className="text-xl font-semibold">{current.title}</h3>
      )}
      {instructions && <p>{instructions}</p>}
      <div className="flex justify-end">
        <Button
          type="button"
          size="auto"
          variant="secondary"
          onClick={() => handleNext(true)}
        >
          ➕ New Exercise
        </Button>
      </div>
      <div className="space-y-6">
        {exercises.map((ex) => (
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
                          submitted ? (
                            <span className="text-gray-400">___</span>
                          ) : answers[ex.id] ? (
                            <span className="text-blue-600">{answers[ex.id]}</span>
                          ) : (
                            <span className="text-gray-400">___</span>
                          )
                        )}
                      </React.Fragment>
                    ))}
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
               {submitted && evaluation[ex.id] !== undefined && (
                <div className="mt-2 text-sm">
                  {String(answers[ex.id]).trim().toLowerCase() ===
                  String(evaluation[ex.id]?.correct).trim().toLowerCase() ? (
                    <span className="text-green-600">✅ Correct!</span>
                  ) : (
                    <>
                      <span className="text-red-600">❌ Incorrect.</span>
                      <div className="mt-1 text-gray-700 dark:text-gray-300">
                        {ex.explanation}
                      </div>
                      <div className="mt-1">
                        {diffWords(answers[ex.id], evaluation[ex.id]?.correct)}
                      </div>
                    </>
                  )}
                  {evaluation[ex.id]?.alternatives &&
                    evaluation[ex.id].alternatives.length > 0 && (
                      <div className="text-sm mt-1 text-blue-600 dark:text-blue-300">
                        Other ways to say it: {evaluation[ex.id].alternatives.join(', ')}
                      </div>
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
        {submitted && !passed && (
          submitting ? (
            <div className="mt-4 flex items-center gap-2">
              <Spinner />
              <span className="italic">AI thinking...</span>
            </div>
          ) : (
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
          )
        )}
        {submitted && passed && (
          <div className="mt-4 flex flex-col sm:flex-row items-start sm:items-center gap-2 text-green-700">
            <span>All exercises correct!</span>
            <Button
              type="button"
              variant="secondary"
              onClick={() => handleNext(true)}
              disabled={loading}
            >
              {loading ? "Loading..." : "More Exercises"}
            </Button>
          </div>
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

import React, { useEffect, useState } from "react";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Spinner from "./UI/Spinner";
import { Input } from "./UI/UI";
import { CheckCircle, XCircle } from "lucide-react";
import {
    getAiExercises,
    saveVocabWords,
    submitExerciseAnswers,
    argueExerciseAnswers,
    sendSupportFeedback,
} from "../api";
import diffWords from "../utils/diffWords";
import AskAiModal from "./AskAiModal";
import ReportExerciseModal from "./ReportExerciseModal";

export default function AIExerciseBlock({
    data,
    blockId = "ai",
    completed = false,
    onComplete,
    mode = "student",
    fetchExercisesFn = getAiExercises,
    setFooterActions,
}) {
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
    const [showAsk, setShowAsk] = useState(false);
    const [reportExerciseId, setReportExerciseId] = useState(null);
    const [replacingId, setReplacingId] = useState(null);

    const exercises = current?.exercises || [];
    const instructions = current?.instructions;
    const feedbackPrompt = current?.feedbackPrompt;
    const showVocab = stage > 1 && Array.isArray(current?.vocabHelp);

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
                    setCurrent("API_ERROR_500");
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

    useEffect(() => {
        if (!setFooterActions) return;

        if (!submitted) {
            setFooterActions(
                <Button
                    type="button"
                    variant="success"
                    size="sm"
                    className="rounded-full"
                    onClick={handleSubmit}
                >
                    Submit Answers
                </Button>
            );
            return () => setFooterActions(null);
        }

        if (!passed) {
            if (submitting) {
                setFooterActions(
                    <div className="flex items-center gap-2">
                        <Spinner />
                        <span className="italic">AI thinking...</span>
                    </div>
                );
            } else {
                setFooterActions(
                    <div className="flex gap-2">
                        <Button
                            type="button"
                            variant="danger"
                            size="sm"
                            className="rounded-full"
                            onClick={handleArgue}
                            disabled={arguing}
                        >
                            {arguing ? "Thinking..." : "Argue with AI"}
                        </Button>
                        <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            className="rounded-full"
                            onClick={handleNext}
                            disabled={loading || arguing}
                        >
                            {loading ? "Loading..." : "Continue"}
                        </Button>
                    </div>
                );
            }
            return () => setFooterActions(null);
        }

        setFooterActions(
            <Button
                type="button"
                variant="secondary"
                size="sm"
                className="rounded-full"
                onClick={() => handleNext(true)}
                disabled={loading}
            >
                {loading ? "Loading..." : "More Exercises"}
            </Button>
        );

        return () => setFooterActions(null);
    }, [submitted, passed, submitting, loading, arguing]);

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
                            [],
                    };
                });
                setEvaluation(map);
            }
            if (result?.feedbackPrompt) {
                setCurrent((prev) => ({ ...prev, feedbackPrompt: result.feedbackPrompt }));
            }
            if (result?.pass) {
                setPassed(true);
                if (Array.isArray(result.results)) {
                    const words = result.results.map((r) => r.correct_answer);
                    await saveVocabWords(words);
                }
            }
        } catch (e) {
            console.error("Submission failed:", e);
        } finally {
            setSubmitting(false);
            fetchNext({ answers });
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
                            [],
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

    const replaceExercise = async (exerciseId) => {
        setReplacingId(exerciseId);
        try {
            const fresh = await fetchExercisesFn();
            const newEx = fresh?.exercises?.[0];
            if (newEx) {
                setCurrent((cur) => {
                    const updated = cur.exercises.map((ex) =>
                        ex.id === exerciseId ? newEx : ex
                    );
                    return { ...cur, exercises: updated };
                });
                setAnswers((a) => {
                    const na = { ...a };
                    delete na[exerciseId];
                    return na;
                });
                setEvaluation((e) => {
                    const ne = { ...e };
                    delete ne[exerciseId];
                    return ne;
                });
            }
        } catch (err) {
            console.error("Failed to replace exercise", err);
        } finally {
            setReplacingId(null);
        }
    };

    const handleSendReport = async (exerciseId, message) => {
        const ex = current.exercises.find((e) => e.id === exerciseId);
        const userAns = answers[exerciseId] || "";
        const aiAns = evaluation[exerciseId]?.correct || "";
        const content =
            `Exercise Report\nID: ${exerciseId}\nQuestion: ${ex?.question}\n` +
            `User Answer: ${userAns}\nAI Answer: ${aiAns}\nMessage: ${message}`;
        await sendSupportFeedback(content);
        await replaceExercise(exerciseId);
    };

    if (mode !== "student") {
        return <Card className="text-center py-4">🤖 AI Exercise</Card>;
    }

    if (loadingInit) {
        return <Card className="text-center py-4">Loading personalized AI exercises...</Card>;
    }

    if (current === "API_ERROR_500") {
        return <Card className="bg-red-100 text-red-800">🚨 500: Mistral API Error.</Card>;
    }

    if (!Array.isArray(exercises)) {
        return <Card className="bg-red-100 text-red-800">Failed to load AI exercise.</Card>;
    }

    return (
        <>
            <Card className="space-y-4">
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
                                        <span className="text-green-600 flex items-center gap-1">
                                            <CheckCircle className="w-4 h-4" />
                                            Correct!
                                        </span>
                                    ) : (
                                        <>
                                            <span className="text-red-600 flex items-center gap-1">
                                                <XCircle className="w-4 h-4" />
                                                Incorrect.
                                            </span>
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
                                    {String(answers[ex.id]).trim().toLowerCase() !==
                                        String(evaluation[ex.id]?.correct).trim().toLowerCase() && (
                                            <div className="mt-2">
                                                <Button
                                                    variant="danger"
                                                    size="sm"
                                                    type="button"
                                                    onClick={() => setReportExerciseId(ex.id)}
                                                    disabled={replacingId === ex.id}
                                                >
                                                    {replacingId === ex.id ? 'Loading...' : 'Report Error'}
                                                </Button>
                                            </div>
                                        )}
                                </div>
                            )}
                        </div>
                    ))}
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
                {submitted && (
                    <>
                        <div className="mt-4 flex gap-2">
                            <Button variant="ghost" type="button" onClick={() => setShowAsk(true)}>
                                Ask AI
                            </Button>
                            {Object.entries(evaluation).some(([id, ev]) => {
                                const userAnswer = answers[id];
                                return (
                                    userAnswer &&
                                    ev?.correct &&
                                    userAnswer.trim().toLowerCase() !==
                                    ev.correct.trim().toLowerCase()
                                );
                            }) && null}
                        </div>
                        {feedbackPrompt && (
                            <div className="mt-4 italic text-blue-700 dark:text-blue-300">
                                {feedbackPrompt}
                            </div>
                        )}
                    </>
                )}

            </Card>
            {showAsk && <AskAiModal onClose={() => setShowAsk(false)} />}
            {reportExerciseId !== null && (
                <ReportExerciseModal
                    exercise={current.exercises.find((e) => e.id === reportExerciseId)}
                    userAnswer={answers[reportExerciseId] || ""}
                    correctAnswer={evaluation[reportExerciseId]?.correct || ""}
                    onSend={(msg) => handleSendReport(reportExerciseId, msg)}
                    onClose={() => setReportExerciseId(null)}
                />
            )}
        </>
    );
}

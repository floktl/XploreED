import React, { useEffect, useState, useRef } from "react";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Spinner from "./UI/Spinner";
import ProgressRing from "./UI/ProgressRing";
import { Input } from "./UI/UI";
import { CheckCircle, XCircle, Brain, BookOpen, Target, Sparkles } from "lucide-react";
import {
    getAiExercises,
    saveVocabWords,
    submitExerciseAnswers,
    argueExerciseAnswers,
    sendSupportFeedback,
} from "../api";
import diffWords from "../utils/diffWords";
import ReportExerciseModal from "./ReportExerciseModal";
import useAppStore from "../store/useAppStore";
import FeedbackBlock from "./FeedbackBlock";

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
    const currentBlockRef = useRef(null);
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
    const [reportExerciseId, setReportExerciseId] = useState(null);
    const [replacingId, setReplacingId] = useState(null);

    // Simulated progress bar states
    const [progressPercentage, setProgressPercentage] = useState(0);
    const [progressStatus, setProgressStatus] = useState("Initializing...");
    const [progressIcon, setProgressIcon] = useState(Brain);

    // Submission progress states
    const [submissionProgress, setSubmissionProgress] = useState(0);
    const [submissionStatus, setSubmissionStatus] = useState("");

    const answersRef = useRef(answers);

    // Background activity tracking
    const addBackgroundActivity = useAppStore((s) => s.addBackgroundActivity);
    const removeBackgroundActivity = useAppStore((s) => s.removeBackgroundActivity);

    // keep answersRef synchronized with state in case other updates setAnswers
    useEffect(() => {
        answersRef.current = answers;
    }, [answers]);

    const exercises = current?.exercises || [];
    const instructions = current?.instructions;
    const feedbackPrompt = current?.feedbackPrompt;
    const showVocab = stage > 1 && Array.isArray(current?.vocabHelp);

    // Check if all exercises have answers
    const allExercisesAnswered = exercises.length > 0 && exercises.every(ex => {
        const answer = answers[ex.id];
        return answer && answer.trim().length > 0;
    });

    useEffect(() => {
        setIsComplete(completed);
    }, [completed]);

    useEffect(() => {
        if (current && Array.isArray(current.exercises) && current.exercises.length > 0) {
            currentBlockRef.current = current;
        }
    }, [current]);

    useEffect(() => {
        if (mode !== "student") return;
        if (!current || !Array.isArray(current.exercises)) {
            setLoadingInit(true);

            // Start progress simulation
            let progress = 0;
            const progressSteps = [
                { percentage: 15, status: "Analyzing your skill level...", icon: Target },
                { percentage: 35, status: "Reviewing your vocabulary...", icon: BookOpen },
                { percentage: 55, status: "Identifying weak areas...", icon: Brain },
                { percentage: 75, status: "Generating personalized exercises...", icon: Sparkles },
                { percentage: 90, status: "Finalizing your lesson...", icon: Sparkles },
                { percentage: 100, status: "Ready!", icon: CheckCircle }
            ];

            let currentStep = 0;
            const progressInterval = setInterval(() => {
                if (currentStep < progressSteps.length) {
                    const step = progressSteps[currentStep];
                    setProgressPercentage(step.percentage);
                    setProgressStatus(step.status);
                    setProgressIcon(step.icon);
                    currentStep++;
                } else {
                    clearInterval(progressInterval);
                }
            }, 800); // Update every 800ms

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
                .finally(() => {
                    clearInterval(progressInterval);
                    setLoadingInit(false);
                });
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
                    disabled={!allExercisesAnswered}
                >
                    {allExercisesAnswered ? "Submit Answers" : `Complete ${exercises.length - Object.keys(answers).filter(k => answers[k] && answers[k].trim().length > 0).length} more answer${exercises.length - Object.keys(answers).filter(k => answers[k] && answers[k].trim().length > 0).length === 1 ? '' : 's'}`}
                </Button>
            );
            return () => setFooterActions(null);
        }

        if (!passed) {
            if (submitting) {
                setFooterActions(
                    <div className="flex items-center gap-2">
                        <Spinner />
                        <span className="italic">Processing...</span>
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
    }, [submitted, passed, submitting, loading, arguing, answers]);

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
        const updated = { ...answersRef.current, [exId]: value };
        answersRef.current = updated;
        setAnswers(updated);
    };

    const handleSubmit = async () => {
        setSubmitting(true);
        setSubmitted(true);

        // Log answers before sending
        console.log("Submitting answers:", answersRef.current);

        // Start submission progress simulation
        const submissionSteps = [
            { percentage: 20, status: "Analyzing your answers..." },
            { percentage: 40, status: "Checking grammar and vocabulary..." },
            { percentage: 60, status: "Generating personalized feedback..." },
            { percentage: 80, status: "Preparing explanations..." },
            { percentage: 100, status: "Evaluation complete!" }
        ];

        let currentStep = 0;
        const submissionInterval = setInterval(() => {
            if (currentStep < submissionSteps.length) {
                const step = submissionSteps[currentStep];
                setSubmissionProgress(step.percentage);
                setSubmissionStatus(step.status);
                currentStep++;
            } else {
                clearInterval(submissionInterval);
            }
        }, 600); // Update every 600ms

        const currentAnswers = answersRef.current;
        try {
            const blockToSubmit = currentBlockRef.current || current;
            const result = await submitExerciseAnswers(blockId, currentAnswers, {
                instructions: blockToSubmit?.instructions || "",
                exercises: blockToSubmit?.exercises || [],
                vocabHelp: blockToSubmit?.vocabHelp || [],
            });

            if (result?.results) {
                // Log the full feedback block for all exercises
                console.log("Full feedback block (result.results):", result.results);
                const map = {};
                result.results.forEach((r) => {
                    map[r.id] = {
                        is_correct: r.is_correct, // <-- Add this line to preserve backend correctness
                        correct: r.correct_answer,
                        alternatives:
                            r.alternatives ||
                            r.other_solutions ||
                            r.other_answers ||
                            [],
                        explanation: r.explanation || "",
                    };
                    // Log feedback for translation exercises
                    if (r.type === "translation") {
                        console.log(`Feedback for translation exercise (id: ${r.id}):`, r);
                    }
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

                    // Add background activity for vocab saving
                    const vocabActivityId = `vocab-${Date.now()}`;
                    addBackgroundActivity({
                        id: vocabActivityId,
                        label: "Saving vocabulary words...",
                        status: "In progress"
                    });

                    try {
                        await saveVocabWords(words);
                        // Update activity status
                        setTimeout(() => removeBackgroundActivity(vocabActivityId), 1200);
                    } catch (error) {
                        console.error("Failed to save vocab:", error);
                        setTimeout(() => removeBackgroundActivity(vocabActivityId), 1200);
                    }
                }
            }
        } catch (e) {
            console.error("Submission failed:", e);
        } finally {
            clearInterval(submissionInterval);
            setSubmitting(false);
            setSubmissionProgress(0);
            setSubmissionStatus("");
            fetchNext({ answers: currentAnswers });
        }
    };

    const handleArgue = async () => {
        setArguing(true);

        // Start arguing progress simulation
        const arguingSteps = [
            { percentage: 25, status: "Reviewing your argument..." },
            { percentage: 50, status: "Re-evaluating the answer..." },
            { percentage: 75, status: "Preparing response..." },
            { percentage: 100, status: "Response ready!" }
        ];

        let currentStep = 0;
        const arguingInterval = setInterval(() => {
            if (currentStep < arguingSteps.length) {
                const step = arguingSteps[currentStep];
                setSubmissionProgress(step.percentage);
                setSubmissionStatus(step.status);
                currentStep++;
            } else {
                clearInterval(arguingInterval);
            }
        }, 500); // Update every 500ms

        try {
            const currentAnswers = answersRef.current;
            const result = await argueExerciseAnswers(blockId, currentAnswers, current);
            if (result?.results) {
                const map = {};
                result.results.forEach((r) => {
                    map[r.id] = {
                        is_correct: r.is_correct, // Preserve backend correctness
                        correct: r.correct_answer,
                        alternatives:
                            r.alternatives ||
                            r.other_solutions ||
                            r.other_answers ||
                            [],
                        explanation: r.explanation || "",
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
            clearInterval(arguingInterval);
            setArguing(false);
            setSubmissionProgress(0);
            setSubmissionStatus("");
        }
    };

    const handleNext = async (force = false) => {
        if (passed && !force) return;
        if (nextExercise) {
            setCurrent(nextExercise);
            setNextExercise(null);
            setStage((s) => s + 1);
            answersRef.current = {};
            setAnswers({});
            setSubmitted(false);
            setEvaluation({});
            setPassed(false);
            setArguing(false);
            fetchNext();
        } else {
            setLoading(true);
            try {
                const currentAnswers = answersRef.current;
                const newData = await fetchExercisesFn({ answers: currentAnswers });
                setCurrent(newData);
                setStage((s) => s + 1);
                answersRef.current = {};
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
                    answersRef.current = na;
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
        const userAns = answersRef.current[exerciseId] || "";
        const aiAns = evaluation[exerciseId]?.correct || "";
        const content =
            `Exercise Report\nID: ${exerciseId}\nQuestion: ${ex?.question}\n` +
            `User Answer: ${userAns}\nAI Answer: ${aiAns}\nMessage: ${message}`;
        await sendSupportFeedback(content);
        await replaceExercise(exerciseId);
    };

    if (mode !== "student") {
        // console.log('[AIExerciseBlock] Not student mode, rendering Card');
        return <Card className="text-center py-4">🤖 AI Exercise</Card>;
    }

    if (loadingInit) {
        // console.log('[AIExerciseBlock] loadingInit true, rendering loading Card');
        const IconComponent = progressIcon;
        return (
            <Card className="text-center py-8">
                <div className="flex justify-center mb-6">
                    <ProgressRing
                        percentage={progressPercentage}
                        size={120}
                        color={progressPercentage === 100 ? "#10B981" : "#3B82F6"}
                    />
                </div>
                <div className="flex items-center justify-center gap-3 mb-4">
                    <IconComponent className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                        {progressStatus}
                    </h3>
                </div>
                <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                    {progressPercentage < 100
                        ? "We're crafting the perfect exercises tailored to your learning needs."
                        : "Your personalized exercises are ready!"
                    }
                </p>
                {progressPercentage < 100 && (
                    <div className="mt-6 flex justify-center">
                        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                            <Spinner />
                            <span>Please wait...</span>
                        </div>
                    </div>
                )}
            </Card>
        );
    }

    if (current === "API_ERROR_500") {
        // console.log('[AIExerciseBlock] API_ERROR_500, rendering error Card');
        return <Card className="bg-red-100 text-red-800">🚨 500: Mistral API Error.</Card>;
    }

    if (!Array.isArray(exercises)) {
        // console.log('[AIExerciseBlock] exercises not array, rendering error Card');
        return <Card className="bg-red-100 text-red-800">Failed to load AI exercise.</Card>;
    }

    // Show submission progress in main content area
    if (submitting) {
        const IconComponent = progressIcon;
        return (
            <Card className="text-center py-8">
                <div className="flex justify-center mb-6">
                    <ProgressRing
                        percentage={submissionProgress}
                        size={120}
                        color={submissionProgress === 100 ? "#10B981" : "#3B82F6"}
                    />
                </div>
                <div className="flex items-center justify-center gap-3 mb-4">
                    <IconComponent className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                        {submissionStatus}
                    </h3>
                </div>
                <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                    {submissionProgress < 100
                        ? "We're analyzing your answers and generating personalized feedback."
                        : "Your evaluation is complete!"
                    }
                </p>
                {submissionProgress < 100 && (
                    <div className="mt-6 flex justify-center">
                        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                            <Spinner />
                            <span>Please wait...</span>
                        </div>
                    </div>
                )}
            </Card>
        );
    }

    // Show arguing progress in main content area
    if (arguing) {
        const IconComponent = progressIcon;
        return (
            <Card className="text-center py-8">
                <div className="flex justify-center mb-6">
                    <ProgressRing
                        percentage={submissionProgress}
                        size={120}
                        color={submissionProgress === 100 ? "#10B981" : "#EF4444"}
                    />
                </div>
                <div className="flex items-center justify-center gap-3 mb-4">
                    <IconComponent className="w-6 h-6 text-red-600 dark:text-red-400" />
                    <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                        {submissionStatus}
                    </h3>
                </div>
                <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                    {submissionProgress < 100
                        ? "We're reviewing your argument and re-evaluating the answer."
                        : "Response ready!"
                    }
                </p>
                {submissionProgress < 100 && (
                    <div className="mt-6 flex justify-center">
                        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                            <Spinner />
                            <span>Please wait...</span>
                        </div>
                    </div>
                )}
            </Card>
        );
    }

    // console.log('[AIExerciseBlock] RENDERING OUTERMOST DIV WITH data-tour=ai-feedback');
    return (
        <div data-tour="ai-feedback">
            {/* Sticky progress bar directly under header, above Card */}
            {!submitted && exercises.length > 0 && (
                <div className="sticky top-16 z-30 w-full bg-white dark:bg-gray-900" style={{marginBottom: '1.5rem'}}>
                    <div className="w-full h-2 rounded-full bg-gray-200 dark:bg-gray-800">
                        <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{
                                width: `${(Object.keys(answers).filter(k => answers[k] && answers[k].trim().length > 0).length / exercises.length) * 100}%`
                            }}
                        ></div>
                    </div>
                </div>
            )}
            <Card className="space-y-4">

                {stage === 1 && current.title && (
                    <h3 className="text-xl font-semibold">{current.title}</h3>
                )}
                {instructions && <p>{instructions}</p>}

                <div className="space-y-6">
                    {exercises.map((ex) => {
                        const hasAnswer = answers[ex.id] && answers[ex.id].trim().length > 0;
                        const isIncomplete = !submitted && !hasAnswer;

                        return (
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
                                            {ex.options.map((opt, idx) => (
                                                <Button
                                                    key={opt + '-' + idx}
                                                    variant={answers[ex.id] === opt ? "primary" : "secondary"}
                                                    type="button"
                                                    onClick={() => handleSelect(ex.id, opt)}
                                                    disabled={submitted}
                                                >
                                                    {opt}
                                                </Button>
                                            ))}
                                        </div>
                                        {isIncomplete && (
                                            null
                                        )}
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
                                            className={isIncomplete ? 'border-orange-400 focus:border-orange-500' : ''}
                                        />
                                        {isIncomplete && (
                                            null
                                        )}
                                    </>
                                )}
                            {submitted && evaluation[ex.id] !== undefined && (
                                <div className="mt-2">
                                    <FeedbackBlock
                                        status={evaluation[ex.id]?.is_correct ? "correct" : "incorrect"}
                                        {...(!evaluation[ex.id]?.is_correct && { correct: evaluation[ex.id]?.correct })}
                                        alternatives={evaluation[ex.id]?.alternatives}
                                        explanation={evaluation[ex.id]?.explanation}
                                        userAnswer={answers[ex.id]}
                                        {...(!evaluation[ex.id]?.is_correct && { diff: diffWords(answers[ex.id], evaluation[ex.id]?.correct) })}
                                    />
                                </div>
                            )}
                        </div>
                    );
                })}
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
                {submitted && feedbackPrompt && (
                    <div className="mt-4 italic text-blue-700 dark:text-blue-300">
                        {feedbackPrompt}
                    </div>
                )}

            </Card>
            {reportExerciseId !== null && (
                <ReportExerciseModal
                    exercise={current.exercises.find((e) => e.id === reportExerciseId)}
                    userAnswer={answers[reportExerciseId] || ""}
                    correctAnswer={evaluation[reportExerciseId]?.correct || ""}
                    onSend={(msg) => handleSendReport(reportExerciseId, msg)}
                    onClose={() => setReportExerciseId(null)}
                />
            )}
        </div>
    );
}

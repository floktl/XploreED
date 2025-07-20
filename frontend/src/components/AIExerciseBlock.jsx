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
    getEnhancedResults,
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
    const [enhancedResults, setEnhancedResults] = useState(null);
    const [enhancedResultsLoading, setEnhancedResultsLoading] = useState(false);

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
                { percentage: 99, status: "Ready!", icon: CheckCircle }
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
            }, 400); // Update every 400ms for faster response

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
        console.log("[AIExerciseBlock] Starting submission...");
        setSubmitting(true);
        setSubmitted(true);

        // Start submission progress simulation with adaptive timing
        const submissionSteps = [
            { percentage: 25, status: "Analyzing your answers..." },
            { percentage: 50, status: "Evaluating with AI..." },
            { percentage: 75, status: "Generating feedback..." },
            { percentage: 99, status: "Evaluation complete!" }
        ];

        let currentStep = 0;
        let apiCompleted = false;
        let apiResult = null;

        // Start the API call immediately
        const currentAnswers = answersRef.current;
        const apiPromise = (async () => {
            try {
                console.log("[AIExerciseBlock] Starting actual API call...");
                const startTime = Date.now();
                const blockToSubmit = currentBlockRef.current || current;
                const result = await submitExerciseAnswers(blockId, currentAnswers, {
                    instructions: blockToSubmit?.instructions || "",
                    exercises: blockToSubmit?.exercises || [],
                    vocabHelp: blockToSubmit?.vocabHelp || [],
                });
                const endTime = Date.now();
                console.log(`[AIExerciseBlock] API call completed in ${endTime - startTime}ms`);
                apiResult = result;
                apiCompleted = true;
            } catch (e) {
                console.error("Submission failed:", e);
                apiCompleted = true;
            }
        })();

        // Progress simulation that adapts to API completion
        const submissionInterval = setInterval(() => {
            if (currentStep < submissionSteps.length) {
                const step = submissionSteps[currentStep];
                console.log(`[AIExerciseBlock] Progress simulation: ${step.percentage}% - ${step.status}`);
                setSubmissionProgress(step.percentage);
                setSubmissionStatus(step.status);
                currentStep++;
            } else {
                // If API is still running, keep showing 99% with spinner
                if (!apiCompleted) {
                    console.log("[AIExerciseBlock] Progress simulation complete, waiting for API...");
                    setSubmissionProgress(99);
                    setSubmissionStatus("Finalizing...");
                } else {
                    console.log("[AIExerciseBlock] Both progress and API complete, clearing interval");
                    clearInterval(submissionInterval);
                    processResults();
                }
            }
        }, 300); // Update every 300ms for faster response

        // Check if API completes before progress simulation
        const checkApiCompletion = setInterval(() => {
            if (apiCompleted) {
                clearInterval(checkApiCompletion);
                if (currentStep >= submissionSteps.length) {
                    // Progress simulation is also complete
                    clearInterval(submissionInterval);
                    processResults();
                }
                // Otherwise, let the progress simulation continue
            }
        }, 100);

        const processResults = () => {
            if (apiResult?.results) {
                console.log("[AIExerciseBlock] Processing results...");
                const map = {};
                apiResult.results.forEach((r) => {
                    map[r.id] = {
                        is_correct: r.is_correct,
                        correct: r.correct_answer,
                        alternatives:
                            r.alternatives ||
                            r.other_solutions ||
                            r.other_answers ||
                            [],
                        explanation: r.explanation || "",
                        loading: r.loading || false,  // Add loading state
                    };
                });
                setEvaluation(map);
                console.log("[AIExerciseBlock] Results set in state");

                // If this is a streaming response, start polling for enhanced results
                if (apiResult.streaming) {
                    console.log("[AIExerciseBlock] Streaming response detected, starting enhanced results polling");
                    startEnhancedResultsPolling();
                }
            }

            if (apiResult?.pass) {
                console.log("[AIExerciseBlock] Exercise passed, saving vocab...");
                setPassed(true);
                if (Array.isArray(apiResult.results)) {
                    const words = apiResult.results.map((r) => r.correct_answer);

                    // Add background activity for vocab saving
                    const vocabActivityId = `vocab-${Date.now()}`;
                    addBackgroundActivity({
                        id: vocabActivityId,
                        label: "Saving vocabulary words...",
                        status: "In progress"
                    });

                    try {
                        saveVocabWords(words).then(() => {
                            setTimeout(() => removeBackgroundActivity(vocabActivityId), 1200);
                        }).catch((error) => {
                            console.error("Failed to save vocab:", error);
                            setTimeout(() => removeBackgroundActivity(vocabActivityId), 1200);
                        });
                    } catch (error) {
                        console.error("Failed to save vocab:", error);
                        setTimeout(() => removeBackgroundActivity(vocabActivityId), 1200);
                    }
                }
            }

            console.log("[AIExerciseBlock] Processing complete, resetting state");
            setSubmitting(false);
            setSubmissionProgress(0);
            setSubmissionStatus("");
            fetchNext({ answers: currentAnswers });
        };

        const startEnhancedResultsPolling = () => {
            console.log("[AIExerciseBlock] Starting enhanced results polling...");
            setEnhancedResultsLoading(true);

            const pollInterval = setInterval(async () => {
                try {
                    const enhancedData = await getEnhancedResults(blockId);
                    console.log("[AIExerciseBlock] Enhanced results status:", enhancedData.status);
                    console.log("[AIExerciseBlock] Enhanced data received:", enhancedData);

                    if (enhancedData.status === "complete" && enhancedData.results) {
                        console.log("[AIExerciseBlock] Enhanced results received, updating UI");
                        console.log("[AIExerciseBlock] Number of results:", enhancedData.results.length);

                        // Log each result to see what's in it
                        enhancedData.results.forEach((result, index) => {
                            console.log(`[AIExerciseBlock] Result ${index}:`, {
                                id: result.id,
                                alternatives: result.alternatives,
                                explanation: result.explanation,
                                alternativesLength: result.alternatives?.length || 0,
                                explanationLength: result.explanation?.length || 0
                            });
                        });

                        setEnhancedResults(enhancedData.results);
                        setEnhancedResultsLoading(false);
                        clearInterval(pollInterval);

                        // Update the evaluation map with enhanced data
                        const enhancedMap = {};
                        enhancedData.results.forEach((r) => {
                            enhancedMap[r.id] = {
                                is_correct: r.is_correct,
                                correct: r.correct_answer,
                                alternatives: r.alternatives || [],
                                explanation: r.explanation || "",
                                loading: false,  // Remove loading state
                            };
                        });

                        console.log("[AIExerciseBlock] Enhanced map created:", enhancedMap);
                        setEvaluation(enhancedMap);



                        if (enhancedData.pass !== undefined) {
                            console.log("[AIExerciseBlock] Setting enhanced pass status:", enhancedData.pass);
                            setPassed(enhancedData.pass);
                        }
                    } else if (enhancedData.status === "processing" && enhancedData.results) {
                        // Progressive update: update each exercise individually as it becomes available
                        console.log("[AIExerciseBlock] Progressive update - checking individual exercises");

                        const currentEvaluation = { ...evaluation };
                        let hasUpdates = false;

                        enhancedData.results.forEach((result) => {
                            const hasAlternatives = result.alternatives && result.alternatives.length > 0;
                            const hasExplanation = result.explanation && result.explanation.length > 0;

                            if (hasAlternatives || hasExplanation) {
                                console.log(`[AIExerciseBlock] Progressive update for ${result.id}:`, {
                                    alternatives: result.alternatives,
                                    explanation: result.explanation
                                });

                                currentEvaluation[result.id] = {
                                    is_correct: result.is_correct,
                                    correct: result.correct_answer,
                                    alternatives: result.alternatives || [],
                                    explanation: result.explanation || "",
                                    loading: false,  // Remove loading state
                                };
                                hasUpdates = true;
                            }
                        });

                        if (hasUpdates) {
                            console.log("[AIExerciseBlock] Progressive update applied:", currentEvaluation);
                            setEvaluation(currentEvaluation);
                        }
                    }
                } catch (error) {
                    console.error("[AIExerciseBlock] Failed to fetch enhanced results:", error);
                    // Continue polling on error
                }
            }, 1000); // Poll every second

            // Stop polling after 15 seconds to avoid infinite polling
            setTimeout(() => {
                clearInterval(pollInterval);
                setEnhancedResultsLoading(false);
                console.log("[AIExerciseBlock] Enhanced results polling timeout");
            }, 15000); // Reduced from 30000 to 15000
        };
    };

    const handleArgue = async () => {
        setArguing(true);

        // Start arguing progress simulation
        const arguingSteps = [
            { percentage: 20, status: "Reviewing your argument..." },
            { percentage: 40, status: "Re-evaluating the answer..." },
            { percentage: 60, status: "Consulting AI analysis..." },
            { percentage: 80, status: "Preparing response..." },
            { percentage: 99, status: "Response ready!" }
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
        }, 300); // Update every 300ms for faster response

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
        return <Card className="text-center py-4">🤖 AI Exercise</Card>;
    }

    if (loadingInit) {
        const IconComponent = progressIcon;
        return (
            <Card className="text-center py-8">
                <div className="flex justify-center mb-6">
                    <ProgressRing
                        percentage={progressPercentage}
                        size={120}
                        color={progressPercentage === 99 ? "#10B981" : "#3B82F6"}
                    />
                </div>
                <div className="flex items-center justify-center gap-3 mb-4">
                    <IconComponent className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                        {progressStatus}
                    </h3>
                </div>
                <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                    {progressPercentage < 99
                        ? "We're crafting the perfect exercises tailored to your learning needs."
                        : "Your personalized exercises are ready!"
                    }
                </p>
                {progressPercentage < 99 && (
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
        return <Card className="bg-red-100 text-red-800">🚨 500: Mistral API Error.</Card>;
    }

    if (!Array.isArray(exercises)) {
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
                        color={submissionProgress === 99 ? "#10B981" : "#3B82F6"}
                    />
                </div>
                <div className="flex items-center justify-center gap-3 mb-4">
                    <IconComponent className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                        {submissionStatus}
                    </h3>
                </div>
                <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                    {submissionProgress < 99
                        ? "We're analyzing your answers and generating personalized feedback."
                        : "Your evaluation is complete!"
                    }
                </p>
                {submissionProgress < 99 && (
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
                        color={submissionProgress === 99 ? "#10B981" : "#EF4444"}
                    />
                </div>
                <div className="flex items-center justify-center gap-3 mb-4">
                    <IconComponent className="w-6 h-6 text-red-600 dark:text-red-400" />
                    <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                        {submissionStatus}
                    </h3>
                </div>
                <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                    {submissionProgress < 99
                        ? "We're reviewing your argument and re-evaluating the answer."
                        : "Response ready!"
                    }
                </p>
                {submissionProgress < 99 && (
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
                                        loading={enhancedResultsLoading && (!evaluation[ex.id]?.alternatives?.length && !evaluation[ex.id]?.explanation)}
                                        exerciseLoading={evaluation[ex.id]?.loading || false}
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


                {enhancedResultsLoading && (
                    <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                        <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300 text-sm">
                            <Spinner size="sm" />
                            <span>Generating detailed explanations and alternative answers...</span>
                        </div>
                        <div className="mt-2 text-xs text-blue-600 dark:text-blue-400">
                            {Object.values(evaluation).filter(e => !e.loading).length} of {exercises.length} exercises evaluated
                        </div>
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

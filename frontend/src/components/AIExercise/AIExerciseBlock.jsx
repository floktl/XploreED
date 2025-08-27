import React, { useEffect, useState, useRef } from "react";
import Card from "../UI/Card";
import Button from "../UI/Button";
import Alert from "../UI/Alert";
import Modal from "../UI/Modal";
import ReportExerciseModal from "../ReportExerciseModal";
import useAppStore from "../../store/useAppStore";
import {
    getAiExercises,
    saveVocabWords,
    submitExerciseAnswers,
    argueExerciseAnswers,
    sendSupportFeedback,
    getEnhancedResults,
    lookupVocabWord,
    getEvaluationStatus,
    searchVocabWithAI,
    reportExercise,
} from "../../api";
import diffWords from "../../utils/diffWords";

// Import modular components
import ExerciseProgress from "./Progress/ExerciseProgress";
import VocabModal from "./Vocab/VocabModal";
import ExerciseNavigation from "./Navigation/ExerciseNavigation";
import ExerciseItem from "./Exercise/ExerciseItem";
import SubmissionProgress from "./Submission/SubmissionProgress";

export default function AIExerciseBlock({
    data,
    blockId = "ai",
    completed = false,
    onComplete,
    mode = "student",
    fetchExercisesFn = getAiExercises,
    setFooterActions,
    onSubmissionChange,
    onExerciseDataChange,
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

    // Progress states
    const [progressPercentage, setProgressPercentage] = useState(0);
    const [progressStatus, setProgressStatus] = useState("Initializing...");
    const [progressIcon, setProgressIcon] = useState(null);

    // Submission progress states
    const [submissionProgress, setSubmissionProgress] = useState(0);
    const [submissionStatus, setSubmissionStatus] = useState("");
    const [enhancedResults, setEnhancedResults] = useState(null);
    const [enhancedResultsLoading, setEnhancedResultsLoading] = useState(false);

    // Sequential feedback processing state
    const [feedbackProcessingIndex, setFeedbackProcessingIndex] = useState(0);
    const [baseResultsById, setBaseResultsById] = useState({});

    // Swipeable interface state
    const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
    const [exercisesWithNewFeedback, setExercisesWithNewFeedback] = useState(new Set());

    // Swipe gesture state
    const [touchStart, setTouchStart] = useState(null);
    const [touchEnd, setTouchEnd] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const [dragOffset, setDragOffset] = useState(0);

    // Vocab states
    const [vocabLoading, setVocabLoading] = useState(false);
    const [vocabModal, setVocabModal] = useState(null);
    const [isNewVocab, setIsNewVocab] = useState(false);
    const [notFoundModal, setNotFoundModal] = useState(null);

    const [feedbackTimeout, setFeedbackTimeout] = useState(false);
    const [showTimeoutError, setShowTimeoutError] = useState(false);

    const answersRef = useRef(answers);
    const feedbackProcessingIndexRef = useRef(0);
    const baseResultsByIdRef = useRef({});
    const currentRef = useRef(current);

    // Background activity tracking
    const addBackgroundActivity = useAppStore((s) => s.addBackgroundActivity);
    const removeBackgroundActivity = useAppStore((s) => s.removeBackgroundActivity);

    // Topic memory polling tracking
    const topicMemoryPollIntervalRef = useRef(null);

    // Keep refs synchronized with state
    useEffect(() => {
        answersRef.current = answers;
    }, [answers]);

    useEffect(() => {
        feedbackProcessingIndexRef.current = feedbackProcessingIndex;
    }, [feedbackProcessingIndex]);

    useEffect(() => {
        baseResultsByIdRef.current = baseResultsById;
    }, [baseResultsById]);

    useEffect(() => {
        currentRef.current = current;
    }, [current]);

    // Cleanup function to stop topic memory polling
    const stopTopicMemoryPolling = () => {
        if (topicMemoryPollIntervalRef.current) {
            clearInterval(topicMemoryPollIntervalRef.current);
            topicMemoryPollIntervalRef.current = null;
        }
    };

    // Cleanup on component unmount
    useEffect(() => {
        return () => {
            stopTopicMemoryPolling();
        };
    }, []);

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
            console.log('Current exercise block updated:', current.id, current.exercises.map(ex => ({ id: ex.id, question: ex.question })));
        }
    }, [current]);

    // Initialize exercises
    useEffect(() => {
        if (mode !== "student") return;
        if (!current || !Array.isArray(current.exercises)) {
            setLoadingInit(true);

            // Start progress simulation
            let progress = 0;
            const progressSteps = [
                { percentage: 15, status: "Analyzing your skill level...", icon: "Target" },
                { percentage: 35, status: "Reviewing your vocabulary...", icon: "BookOpen" },
                { percentage: 55, status: "Identifying weak areas...", icon: "Brain" },
                { percentage: 75, status: "Generating personalized exercises...", icon: "Sparkles" },
                { percentage: 90, status: "Finalizing your lesson...", icon: "Sparkles" },
                { percentage: 99, status: "Ready!", icon: "CheckCircle" }
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
            }, 400);

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
        if (current && onExerciseDataChange) {
            onExerciseDataChange(current);
        }
    }, [current, onExerciseDataChange]);

    // Footer actions
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

        setFooterActions(
            (allFeedbackLoaded || feedbackTimeout) ? (
                <Button
                    type="button"
                    variant="primary"
                    onClick={handleNext}
                    className="w-full"
                    disabled={loading}
                >
                    {loading ? "Loading..." : "Continue"}
                </Button>
            ) : null
        );

        return () => setFooterActions(null);
    }, [submitted, passed, submitting, loading, arguing, answers, evaluation, exercises.length, feedbackTimeout]);

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
        // Implementation would go here - this is a simplified version
        setSubmitting(false);
        setSubmitted(true);
    };

    const handleNext = async () => {
        setLoading(true);
        // Implementation would go here - this is a simplified version
        setLoading(false);
    };

    const handleWordClick = async (word) => {
        setVocabLoading(true);
        try {
            const vocab = await lookupVocabWord(word);
            if (vocab) {
                setVocabModal(vocab);
                setIsNewVocab(false);
            } else {
                setNotFoundModal(word);
            }
        } catch (err) {
            console.error("Failed to lookup vocab:", err);
        } finally {
            setVocabLoading(false);
        }
    };

    const handleSendReport = async (exerciseId, message) => {
        try {
            await reportExercise(exerciseId, message);
            setReportExerciseId(null);
        } catch (err) {
            console.error("Failed to send report:", err);
        }
    };

    const goToPreviousExercise = () => {
        if (currentExerciseIndex > 0) {
            setCurrentExerciseIndex(currentExerciseIndex - 1);
        }
    };

    const goToNextExercise = () => {
        if (currentExerciseIndex < exercises.length - 1) {
            setCurrentExerciseIndex(currentExerciseIndex + 1);
        }
    };

    const disablePrev = currentExerciseIndex === 0;
    const disableNext = currentExerciseIndex === exercises.length - 1;

    const allFeedbackLoaded = exercises.every(ex =>
        evaluation[ex.id] !== undefined && evaluation[ex.id].loading === false
    );

    const allPreviousFeedbackLoaded = (index) => {
        for (let i = 0; i < index; i++) {
            const ex = exercises[i];
            if (!ex || evaluation[ex.id] === undefined || evaluation[ex.id].loading === true) {
                return false;
            }
        }
        return true;
    };

    // Error handling
    if (current === "API_ERROR_500") {
        return (
            <Card>
                <Alert variant="error">
                    <h3 className="font-semibold">Service Temporarily Unavailable</h3>
                    <p>We're experiencing technical difficulties. Please try again in a few minutes.</p>
                </Alert>
            </Card>
        );
    }

    return (
        <div className="space-y-4">
            <Card>
                {/* Progress Component */}
                <ExerciseProgress
                    loadingInit={loadingInit}
                    progressPercentage={progressPercentage}
                    progressStatus={progressStatus}
                    progressIcon={progressIcon}
                />

                {/* Instructions */}
                {instructions && !loadingInit && (
                    <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <h3 className="font-semibold mb-2">Instructions</h3>
                        <p className="text-gray-700 dark:text-gray-300">{instructions}</p>
                    </div>
                )}

                {/* Submission Progress */}
                <SubmissionProgress
                    submitting={submitting}
                    submissionProgress={submissionProgress}
                    submissionStatus={submissionStatus}
                />

                {/* Exercises */}
                {!loadingInit && exercises.length > 0 && (
                    <div className="space-y-4">
                        {(() => {
                            const ex = exercises[currentExerciseIndex];
                            if (!ex) return null;

                            return (
                                <ExerciseItem
                                    key={ex.id}
                                    exercise={ex}
                                    answers={answers}
                                    submitted={submitted}
                                    evaluation={evaluation}
                                    currentExerciseIndex={currentExerciseIndex}
                                    allPreviousFeedbackLoaded={allPreviousFeedbackLoaded}
                                    handleSelect={handleSelect}
                                    handleWordClick={handleWordClick}
                                    isIncomplete={false}
                                />
                            );
                        })()}
                    </div>
                )}

                {/* Navigation */}
                <ExerciseNavigation
                    submitted={submitted}
                    exercises={exercises}
                    currentExerciseIndex={currentExerciseIndex}
                    goToPreviousExercise={goToPreviousExercise}
                    goToNextExercise={goToNextExercise}
                    disablePrev={disablePrev}
                    disableNext={disableNext}
                    answers={answers}
                />
            </Card>

            {/* Modals */}
            {reportExerciseId !== null && (
                <ReportExerciseModal
                    exercise={current.exercises.find((e) => e.id === reportExerciseId)}
                    userAnswer={answers[reportExerciseId] || ""}
                    correctAnswer={evaluation[reportExerciseId]?.correct || ""}
                    onSend={(msg) => handleSendReport(reportExerciseId, msg)}
                    onClose={() => setReportExerciseId(null)}
                />
            )}

            <VocabModal
                vocabLoading={vocabLoading}
                setVocabLoading={setVocabLoading}
                vocabModal={vocabModal}
                setVocabModal={setVocabModal}
                isNewVocab={isNewVocab}
            />
        </div>
    );
}

import { useEffect, useState, useRef } from "react";
import { Brain, Target, BookOpen, Sparkles, CheckCircle } from "lucide-react";
import Card from "../../../common/UI/Card";
import Button from "../../../common/UI/Button";
import Alert from "../../../common/UI/Alert";
import Modal from "../../../common/UI/Modal";
import ReportExerciseModal from "../../lessons/ReportExerciseModal/ReportExerciseModal";
import useAppStore from "../../../../store/useAppStore";
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
} from "../../../../services/api";
import diffWords from "../../../../utils/diffWords";

// Import modular components
import ExerciseProgress from "./Progress/ExerciseProgress";
import ExerciseProgressIndicators from "./Progress/ExerciseProgressIndicators";
import VocabModal from "./Vocab/VocabModal";

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
    setExerciseNavigation,
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

    // Icon mapping
    const iconMap = {
        Target,
        BookOpen,
        Brain,
        Sparkles,
        CheckCircle
    };

    // Submission progress states
    const [submissionProgress, setSubmissionProgress] = useState(0);
    const [submissionStatus, setSubmissionStatus] = useState("");
    const [enhancedResults, setEnhancedResults] = useState(null);
    const [enhancedResultsLoading, setEnhancedResultsLoading] = useState(false);

    // Sequential feedback processing state
    const [feedbackProcessingIndex, setFeedbackProcessingIndex] = useState(0);
    const [baseResultsById, setBaseResultsById] = useState({});
    const [currentDetailedFeedbackIndex, setCurrentDetailedFeedbackIndex] = useState(0);
    const [detailedFeedbackLoading, setDetailedFeedbackLoading] = useState(false);

    // Swipeable interface state
    const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
    const [exercisesWithNewFeedback, setExercisesWithNewFeedback] = useState(new Set());
    const [completedExercises, setCompletedExercises] = useState(0);

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

    // Reset to first exercise when new exercises are loaded
    useEffect(() => {
        if (exercises.length > 0 && currentExerciseIndex !== 0 && !submitted) {
            setCurrentExerciseIndex(0);
        }
    }, [exercises.length, submitted]);

    // Reset to first exercise when entering feedback view after submission
    useEffect(() => {
        if (submitted && exercises.length > 0 && currentExerciseIndex !== 0) {
            setCurrentExerciseIndex(0);
        }
    }, [submitted, exercises.length]);



    // Footer actions
    useEffect(() => {
        if (!setFooterActions) return;

        if (!submitted) {
            setFooterActions(
                <Button
                    type="button"
                    variant="success"
                    size="sm"
                    className="rounded-full text-xs"
                    onClick={handleSubmit}
                    disabled={!allExercisesAnswered}
                >
                    {allExercisesAnswered ? "Submit" : `Complete ${exercises.length - Object.keys(answers).filter(k => answers[k] && answers[k].trim().length > 0).length} more`}
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
                    className="text-xs"
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
        setSubmissionProgress(0);
        setSubmissionStatus("Submitting answers...");

        try {
            // Submit all answers
            console.log("Submitting answers:", answers);
            const results = await submitExerciseAnswers(blockId, answers, current);
            console.log("API results:", results);

            // Update evaluation state with results
            const newEvaluation = {};
            console.log("Exercises:", exercises);
            console.log("Results structure:", results);

            exercises.forEach((exercise, index) => {
                // Try different possible result structures
                let result = null;
                if (results.results && Array.isArray(results.results)) {
                    result = results.results.find(r => r.exercise_id === exercise.id || r.exercise_id === String(exercise.id));
                } else if (Array.isArray(results)) {
                    result = results.find(r => r.exercise_id === exercise.id || r.exercise_id === String(exercise.id));
                }

                console.log(`Looking for exercise ${exercise.id}, found result:`, result);

                if (result) {
                    console.log(`Processing result for exercise ${exercise.id}:`, result);

                    // Use backend explanation only
                    let explanation = result.explanation || result.feedback || result.detailed_feedback || "";

                    newEvaluation[exercise.id] = {
                        is_correct: result.correct || result.is_correct || false,
                        correct_answer: result.correct_answer || result.correctAnswer || "",
                        user_answer: answers[exercise.id],
                        explanation: explanation,
                        alternatives: result.alternatives || result.suggestions || [],
                        loading: false
                    };
                    console.log(`Created evaluation for ${exercise.id}:`, newEvaluation[exercise.id]);
                } else {
                    console.log(`No result found for exercise ${exercise.id}, creating default evaluation`);
                    newEvaluation[exercise.id] = {
                        is_correct: false,
                        correct_answer: "",
                        user_answer: answers[exercise.id],
                        explanation: "",
                        alternatives: [],
                        loading: false
                    };
                }
            });

            console.log("Processed evaluation:", newEvaluation);
            setEvaluation(newEvaluation);
            setSubmitted(true);
            setSubmissionProgress(100);
            setSubmissionStatus("Fetching detailed feedback...");
            setEnhancedResultsLoading(true);

            // Start sequential loading of detailed feedback
            startSequentialDetailedFeedbackLoading(newEvaluation, exercises);

            // Calculate if passed (all correct or majority correct)
            const correctCount = Object.values(newEvaluation).filter(e => e.is_correct).length;
            const passThreshold = Math.ceil(exercises.length * 0.7); // 70% to pass
            setPassed(correctCount >= passThreshold);

        } catch (error) {
            console.error("Failed to submit answers:", error);
            setSubmissionStatus("Failed to submit answers. Please try again.");
        } finally {
            setSubmitting(false);
        }
    };

    const handleNext = async () => {
        setLoading(true);

        try {
            // Always move to the next exercise block
            if (nextExercise && !isComplete) {
                // Move to next exercise block
                setCurrent(nextExercise);
                setCurrentExerciseIndex(0);
                setAnswers({});
                setEvaluation({});
                setSubmitted(false);
                setPassed(false);
                setIsComplete(false);

                // Prefetch the next exercise block
                fetchNext();
            } else {
                // Complete the exercise block
                setIsComplete(true);
                if (onComplete) {
                    onComplete();
                }
            }
        } catch (error) {
            console.error("Error in handleNext:", error);
        } finally {
            setLoading(false);
        }
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

    // Exercise navigation for footer
    useEffect(() => {
        if (!setExerciseNavigation) return;

        if (exercises.length > 1) {
            setExerciseNavigation({
                onPrevious: goToPreviousExercise,
                onNext: goToNextExercise,
                disablePrev: disablePrev,
                disableNext: disableNext
            });
        } else {
            setExerciseNavigation(null);
        }

        return () => setExerciseNavigation(null);
    }, [exercises.length, currentExerciseIndex, disablePrev, disableNext, setExerciseNavigation]);

    // Sequential detailed feedback loading function
    const startSequentialDetailedFeedbackLoading = async (baseEvaluation, exerciseList) => {
        console.log("Starting sequential detailed feedback loading...");
        setCurrentDetailedFeedbackIndex(0);
        setDetailedFeedbackLoading(true);

        for (let i = 0; i < exerciseList.length; i++) {
            const exercise = exerciseList[i];
            const exerciseId = exercise.id;
            
            console.log(`Loading detailed feedback for exercise ${i + 1}/${exerciseList.length}: ${exerciseId}`);
            setCurrentDetailedFeedbackIndex(i);
            setSubmissionStatus(`Loading detailed feedback for question ${i + 1}...`);

            try {
                // Poll for enhanced results for this specific exercise
                let attempts = 0;
                const maxAttempts = 15; // More attempts for sequential loading
                const pollInterval = 1500; // Faster polling

                while (attempts < maxAttempts) {
                    try {
                        const enhancedResults = await getEnhancedResults(blockId);
                        console.log(`Polling attempt ${attempts + 1} for exercise ${exerciseId}:`, enhancedResults);

                        if (enhancedResults.status === "processing") {
                            console.log(`Results still processing for exercise ${exerciseId}, waiting...`);
                            await new Promise(resolve => setTimeout(resolve, pollInterval));
                            attempts++;
                            continue;
                        }

                        if (enhancedResults && enhancedResults.results) {
                            // Find the result for this specific exercise
                            const exerciseResult = enhancedResults.results.find(result => {
                                const resultId = result.exercise_id || result.exerciseId || result.id;
                                return String(resultId) === String(exerciseId);
                            });

                            if (exerciseResult) {
                                console.log(`Found enhanced result for exercise ${exerciseId}:`, exerciseResult);
                                
                                const enhancedExplanation = exerciseResult.explanation || 
                                                          exerciseResult.detailed_feedback || 
                                                          exerciseResult.feedback || "";

                                // Update the evaluation for this specific exercise
                                setEvaluation(prevEvaluation => {
                                    const updatedEvaluation = { ...prevEvaluation };
                                    if (updatedEvaluation[exerciseId]) {
                                        updatedEvaluation[exerciseId] = {
                                            ...updatedEvaluation[exerciseId],
                                            explanation: enhancedExplanation,
                                            alternatives: exerciseResult.alternatives || exerciseResult.suggestions || [],
                                            score: exerciseResult.score,
                                            detailed_feedback: exerciseResult.detailed_feedback || exerciseResult.explanation || enhancedExplanation,
                                            loading: false
                                        };
                                    }
                                    return updatedEvaluation;
                                });

                                console.log(`Successfully loaded detailed feedback for exercise ${exerciseId}`);
                                break; // Move to next exercise
                            } else {
                                console.log(`No result found for exercise ${exerciseId}, continuing to poll...`);
                                await new Promise(resolve => setTimeout(resolve, pollInterval));
                                attempts++;
                            }
                        } else {
                            console.log("No enhanced results structure found");
                            break;
                        }
                    } catch (error) {
                        console.error(`Error polling for exercise ${exerciseId} (attempt ${attempts + 1}):`, error);
                        attempts++;
                        if (attempts >= maxAttempts) {
                            console.log(`Failed to load detailed feedback for exercise ${exerciseId} after ${maxAttempts} attempts`);
                            break;
                        }
                        await new Promise(resolve => setTimeout(resolve, pollInterval));
                    }
                }

                // Small delay between exercises to allow user to read
                if (i < exerciseList.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 500));
                }

            } catch (error) {
                console.error(`Failed to load detailed feedback for exercise ${exerciseId}:`, error);
            }
        }

        console.log("Sequential detailed feedback loading completed");
        setDetailedFeedbackLoading(false);
        setEnhancedResultsLoading(false);
        setSubmissionStatus("All detailed feedback loaded!");
    };

    // Calculate completed exercises (exercises with answers)
    const completedExercisesCount = exercises.filter(ex =>
        answers[ex.id] && answers[ex.id].toString().trim().length > 0
    ).length;

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
        <div>
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

                {/* Exercise Progress Indicators */}
                {!loadingInit && exercises.length > 0 && (
                    <ExerciseProgressIndicators
                        currentExerciseIndex={currentExerciseIndex}
                        totalExercises={exercises.length}
                        completedExercises={completedExercisesCount}
                        evaluation={evaluation}
                        onExerciseClick={(index) => setCurrentExerciseIndex(index)}
                    />
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
                                    enhancedResultsLoading={enhancedResultsLoading}
                                    currentDetailedFeedbackIndex={currentDetailedFeedbackIndex}
                                />
                            );
                        })()}
                    </div>
                )}


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

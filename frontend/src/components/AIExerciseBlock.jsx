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
    lookupVocabWord,
    getEvaluationStatus,
    searchVocabWithAI,
    reportExercise,
} from "../api";
import diffWords from "../utils/diffWords";
import ReportExerciseModal from "./ReportExerciseModal";
import useAppStore from "../store/useAppStore";
import FeedbackBlock from "./FeedbackBlock";
import VocabDetailModal from "./VocabDetailModal";
import Modal from "./UI/Modal";
import Alert from "./UI/Alert";

function renderClickableText(text, onWordClick) {
  if (!text) return null;
  const parts = text.split(/(\b[\wÄÖÜäöüß]+\b)/g);
  return parts.map((part, i) => {
    if (/^\w+$/u.test(part)) {
      return (
        <span
          key={i}
          className="underline decoration-dotted cursor-pointer hover:text-blue-500"
          onClick={() => onWordClick(part)}
        >
          {part}
        </span>
      );
    }
    return part;
  });
}

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

    // Simulated progress bar states
    const [progressPercentage, setProgressPercentage] = useState(0);
    const [progressStatus, setProgressStatus] = useState("Initializing...");
    const [progressIcon, setProgressIcon] = useState(Brain);

    // Submission progress states
    const [submissionProgress, setSubmissionProgress] = useState(0);
    const [submissionStatus, setSubmissionStatus] = useState("");
    const [enhancedResults, setEnhancedResults] = useState(null);
    const [enhancedResultsLoading, setEnhancedResultsLoading] = useState(false);

    // Swipeable interface state
    const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
    const [exercisesWithNewFeedback, setExercisesWithNewFeedback] = useState(new Set());

    // Swipe gesture state
    const [touchStart, setTouchStart] = useState(null);
    const [touchEnd, setTouchEnd] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const [dragOffset, setDragOffset] = useState(0);

    // Add vocabLoading state for vocab lookup
    const [vocabLoading, setVocabLoading] = useState(false);

    // Add vocabModal and setVocabModal for vocab lookup
    const [vocabModal, setVocabModal] = useState(null);
    const [isNewVocab, setIsNewVocab] = useState(false);

    const [notFoundModal, setNotFoundModal] = useState(null);

    const [feedbackTimeout, setFeedbackTimeout] = useState(false);
    const [showTimeoutError, setShowTimeoutError] = useState(false);

    const answersRef = useRef(answers);

    // Background activity tracking
    const addBackgroundActivity = useAppStore((s) => s.addBackgroundActivity);
    const removeBackgroundActivity = useAppStore((s) => s.removeBackgroundActivity);

    // Topic memory polling tracking
    const topicMemoryPollIntervalRef = useRef(null);

    // keep answersRef synchronized with state in case other updates setAnswers
    useEffect(() => {
        answersRef.current = answers;
    }, [answers]);

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
        if (current && onExerciseDataChange) {
            onExerciseDataChange(current);
        }
    }, [current, onExerciseDataChange]);

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

        // Only show Continue button after submission and when all feedback is loaded or after timeout
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
        setSubmitted(true);
        setCurrentExerciseIndex(0);
        if (onSubmissionChange) {
            onSubmissionChange(true);
        }

        // Stop any existing topic memory polling before starting new submission
        stopTopicMemoryPolling();

        // Add background activity for topic memory processing
        const topicMemoryActivityId = `topic-memory-${Date.now()}`;
        addBackgroundActivity({
            id: topicMemoryActivityId,
            label: "Processing topic memory...",
            status: "active"
        });

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
                const startTime = Date.now();
                const blockToSubmit = currentBlockRef.current || current;
                // Use the actual id from the exercise data, fallback to the prop
                const actualBlockId = blockToSubmit?.id || blockId;

                // Use training-specific submission for training exercises
                const exerciseBlockData = {
                    instructions: blockToSubmit?.instructions || "",
                    exercises: blockToSubmit?.exercises || [],
                    vocabHelp: blockToSubmit?.vocabHelp || [],
                    topic: blockToSubmit?.topic || "general",
                };

                let result;
                result = await submitExerciseAnswers(actualBlockId, currentAnswers, exerciseBlockData);

                const endTime = Date.now();
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
                setSubmissionProgress(step.percentage);
                setSubmissionStatus(step.status);
                currentStep++;
            } else {
                // If API is still running, keep showing 99% with spinner
                if (!apiCompleted) {
                    setSubmissionProgress(99);
                    setSubmissionStatus("Finalizing...");
                } else {
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
                const map = {};
                apiResult.results.forEach((r) => {
                    const resId = r.id || r.exercise_id; // support both shapes
                    if (!resId) return;
                    map[resId] = {
                        is_correct: r.is_correct,
                        correct: r.correct_answer,
                        correct_answer: r.correct_answer,
                        alternatives:
                            r.alternatives ||
                            r.other_solutions ||
                            r.other_answers ||
                            [],
                        explanation: r.explanation || "",
                        user_answer: r.user_answer,
                        loading: true,  // Start with loading state for enhanced feedback
                    };
                });
                setEvaluation(map);

                // Start polling for enhanced results in the background
                // Use the block_id from the API response if available, otherwise fallback
                const responseBlockId = apiResult?.block_id || current?.id || blockId;
                startEnhancedResultsPolling(topicMemoryActivityId, responseBlockId);
            }

            if (apiResult?.pass) {
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

            setSubmitting(false);
            setSubmissionProgress(0);
            setSubmissionStatus("");
            fetchNext({ answers: currentAnswers });
        };

        const startEnhancedResultsPolling = (activityId, blockIdToUse = null) => {
            setEnhancedResultsLoading(true);
            setFeedbackTimeout(false);
            setShowTimeoutError(false);

            // Use the provided block_id, fallback to the exercise data, then to the prop
            const actualBlockId = blockIdToUse || current?.id || blockId;

            const pollInterval = setInterval(async () => {
                try {
                    const enhancedData = await getEnhancedResults(actualBlockId);
                    if (enhancedData.status === "complete" && enhancedData.results) {

                        setEnhancedResults(enhancedData.results);
                        setEnhancedResultsLoading(false);
                        clearInterval(pollInterval);
                        clearTimeout(timeoutId);
                        setFeedbackTimeout(false);

                        // Don't remove topic memory background activity here - keep it active for background processing
                        // removeBackgroundActivity(activityId);

                        // Update the evaluation map with enhanced data
                        const enhancedMap = {};
                        enhancedData.results.forEach((r) => {
                            const resId = r.id || r.exercise_id;
                            if (!resId) return;
                            enhancedMap[resId] = {
                                is_correct: r.is_correct,
                                correct: r.correct_answer,
                                correct_answer: r.correct_answer,
                                user_answer: r.user_answer,
                                alternatives: r.alternatives || [],
                                explanation: r.explanation || "",
                                loading: false,  // Enhanced feedback complete
                            };
                        });

                        setEvaluation(enhancedMap);

                        if (enhancedData.pass !== undefined) {
                            setPassed(enhancedData.pass);
                        }

                        // Start polling for topic memory completion
                        pollForTopicMemoryCompletion(activityId);
                    } else if (enhancedData.status === "processing" && enhancedData.results) {
                        // Progressive update: update each exercise individually as it becomes available
                        const currentEvaluation = { ...evaluation };
                        let hasUpdates = false;

                        enhancedData.results.forEach((result) => {
                            const hasAlternatives = result.alternatives && result.alternatives.length > 0;
                            const hasExplanation = result.explanation && result.explanation.length > 0;

                            // Always update with the latest result data
                            const resId = result.id || result.exercise_id;
                            if (resId) {
                                const existingResult = currentEvaluation[resId];
                                const hasEnhancedContent = hasAlternatives || hasExplanation;

                                // Show results as soon as they have either alternatives OR explanations
                                // Don't wait for both - show partial results immediately
                                if (hasEnhancedContent) {
                                    currentEvaluation[resId] = {
                                        is_correct: result.is_correct,
                                        correct: result.correct_answer,
                                        correct_answer: result.correct_answer,
                                        user_answer: result.user_answer,
                                        alternatives: result.alternatives || [],
                                        explanation: result.explanation || "",
                                        loading: false,  // Remove loading state
                                    };
                                    hasUpdates = true;

                                    // Mark this exercise as having new feedback
                                    const exerciseIndex = exercises.findIndex(ex => ex.id === resId);
                                    if (exerciseIndex !== -1) {
                                        setExercisesWithNewFeedback(prev => new Set([...prev, exerciseIndex]));
                                    }
                                } else if (!existingResult || existingResult.loading) {
                                    // If we have a result but no alternatives/explanation yet, show basic result
                                    currentEvaluation[resId] = {
                                        is_correct: result.is_correct,
                                        correct: result.correct_answer,
                                        correct_answer: result.correct_answer,
                                        user_answer: result.user_answer,
                                        alternatives: [],
                                        explanation: "",
                                        loading: true,  // Keep loading state for basic results
                                    };
                                    hasUpdates = true;
                                }
                            }
                        });

                        if (hasUpdates) {
                            setEvaluation(currentEvaluation);
                        }
                    }
                } catch (error) {
                    console.error("[AIExerciseBlock] Failed to fetch enhanced results:", error);
                    // Continue polling on error, but remove background activity after multiple failures
                    if (error.message && error.message.includes("Failed to fetch")) {
                        // If it's a network error, remove background activity after a few attempts
                        setTimeout(() => removeBackgroundActivity(activityId), 5000);
                    }
                }
            }, 1000); // Poll every 1 second to match backend timing

            let timeoutId = setTimeout(() => {
                clearInterval(pollInterval);
                setEnhancedResultsLoading(false);
                const allDone = Object.values(evaluation).every(res => !res?.loading ?? true);
                if (!allDone) {
                    setFeedbackTimeout(true);
                    setShowTimeoutError(true);
                }
                // Remove topic memory background activity on timeout
                removeBackgroundActivity(activityId);
            }, 15000);
        };

        const pollForTopicMemoryCompletion = (activityId) => {
            // Clear any existing polling interval
            if (topicMemoryPollIntervalRef.current) {
                clearInterval(topicMemoryPollIntervalRef.current);
            }

            let pollCount = 0;
            let isCompleted = false; // Flag to prevent further polling after completion

            // Poll for topic memory completion status
            topicMemoryPollIntervalRef.current = setInterval(async () => {
                // Check if already completed to prevent race conditions
                if (isCompleted) {
                    return;
                }

                pollCount++;

                try {
                    // Check if topic memory processing is complete by looking for the completion message
                    // We'll check the backend logs or a completion endpoint
                                // Use the actual id from the exercise data, fallback to the prop
            const actualBlockId = current?.id || blockId;
                    const response = await fetch(`/api/ai-exercise/${actualBlockId}/topic-memory-status`, {
                        credentials: "include",
                    });

                    if (response.ok) {
                        const statusData = await response.json();

                        if (statusData.topic_memory_updated || statusData.update_status === "completed") {
                            isCompleted = true; // Set flag to prevent further polling
                            clearInterval(topicMemoryPollIntervalRef.current);
                            topicMemoryPollIntervalRef.current = null;
                            removeBackgroundActivity(activityId);
                            return;
                        }
                    }
                } catch (error) {
                    console.error("[AIExerciseBlock] Failed to check topic memory status:", error);
                    // Continue polling on error - don't stop the spinner
                }
            }, 3000); // Check every 3 seconds for completion

            // Add a fallback timeout to prevent infinite polling
            setTimeout(() => {
                if (topicMemoryPollIntervalRef.current && !isCompleted) {
                    isCompleted = true; // Set flag to prevent further polling
                    clearInterval(topicMemoryPollIntervalRef.current);
                    topicMemoryPollIntervalRef.current = null;
                    removeBackgroundActivity(activityId);
                }
            }, 30000); // 30 second fallback timeout
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
            // Use the actual id from the exercise data, fallback to the prop
            const actualBlockId = current?.id || blockId;
            const result = await argueExerciseAnswers(actualBlockId, currentAnswers, current);
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
                // Always force generation of new block when continuing
                const newData = await fetchExercisesFn({ force_new: true });
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

    // Swipeable interface navigation functions
    const goToNextExercise = () => {
        if (currentExerciseIndex < exercises.length - 1) {
            setCurrentExerciseIndex(currentExerciseIndex + 1);
        }
    };

    const goToPreviousExercise = () => {
        if (currentExerciseIndex > 0) {
            setCurrentExerciseIndex(currentExerciseIndex - 1);
        }
    };

    const goToExercise = (index) => {
        if (index >= 0 && index < exercises.length) {
            setCurrentExerciseIndex(index);
        }
    };

                        // Progress bar click handler - segmented navigation
    const handleProgressBarClick = (event) => {
        event.preventDefault();
        event.stopPropagation();

        if (exercises.length <= 1) {
            return;
        }

        const rect = event.currentTarget.getBoundingClientRect();
        const clickX = event.clientX - rect.left;
        const progressBarWidth = rect.width;
        const clickPercentage = clickX / progressBarWidth;

        // Calculate which exercise to go to based on click position
        const targetIndex = Math.floor(clickPercentage * exercises.length);
        const clampedIndex = Math.max(0, Math.min(targetIndex, exercises.length - 1));

        goToExercise(clampedIndex);
    };

        // Swipe gesture handlers with live dragging
    const onTouchStart = (e) => {
        setTouchEnd(null);
        setTouchStart(e.targetTouches[0].clientX);
        setIsDragging(true);
        setDragOffset(0);
    };

    const onTouchMove = (e) => {
        if (!isDragging) return;

        const currentX = e.targetTouches[0].clientX;
        setTouchEnd(currentX);

        if (touchStart) {
            const offset = currentX - touchStart;
            setDragOffset(offset);
        }
    };

                const onTouchEnd = () => {
            if (!touchStart || !touchEnd) {
                setIsDragging(false);
                setDragOffset(0);
                return;
            }

            const distance = touchStart - touchEnd;
            const isLeftSwipe = distance > 30; // Reduced threshold for easier swiping
            const isRightSwipe = distance < -30; // Reduced threshold for easier swiping

            if (isLeftSwipe && currentExerciseIndex < exercises.length - 1) {
                goToNextExercise();
            } else if (isRightSwipe && currentExerciseIndex > 0) {
                goToPreviousExercise();
            }

            setIsDragging(false);
            setDragOffset(0);
        };

    // Mouse drag handlers for desktop
    const onMouseDown = (e) => {
        setTouchEnd(null);
        setTouchStart(e.clientX);
        setIsDragging(true);
        setDragOffset(0);
    };

    const onMouseMove = (e) => {
        if (!isDragging) return;

        const currentX = e.clientX;
        setTouchEnd(currentX);

        if (touchStart) {
            const offset = currentX - touchStart;
            setDragOffset(offset);
        }
    };

    const onMouseUp = () => {
        if (!touchStart || !touchEnd) {
            setIsDragging(false);
            setDragOffset(0);
            return;
        }

        const distance = touchStart - touchEnd;
        const isLeftSwipe = distance > 30; // Reduced threshold for easier swiping
        const isRightSwipe = distance < -30; // Reduced threshold for easier swiping

        if (isLeftSwipe && currentExerciseIndex < exercises.length - 1) {
            goToNextExercise();
        } else if (isRightSwipe && currentExerciseIndex > 0) {
            goToPreviousExercise();
        }

        setIsDragging(false);
        setDragOffset(0);
    };

    // Keyboard navigation
    useEffect(() => {
        if (!submitted || exercises.length <= 1) return;

        const handleKeyDown = (event) => {
            if (event.key === 'ArrowLeft') {
                event.preventDefault();
                goToPreviousExercise();
            } else if (event.key === 'ArrowRight') {
                event.preventDefault();
                goToNextExercise();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [submitted, exercises.length, currentExerciseIndex]);

    // Helper to check if feedback for an exercise is fully loaded
    const isFeedbackLoaded = (idx) => {
        const ex = exercises[idx];
        if (!ex) return false;
        const evalObj = evaluation[ex.id];
        return evalObj && evalObj.loading === false;
    };

    // Helper to check if all feedback up to a given index is loaded
    const allPreviousFeedbackLoaded = (idx) => {
        for (let i = 0; i < idx; i++) {
            if (!isFeedbackLoaded(i)) return false;
        }
        return true;
    };

    // Helper: Check if all feedback is loaded
    const allFeedbackLoaded = exercises.length > 0 && exercises.every(ex => evaluation[ex.id] && !evaluation[ex.id].loading);

    // Update navigation functions
    const disableNext = !isFeedbackLoaded(currentExerciseIndex);
    const disablePrev = currentExerciseIndex === 0;

    // Define the handler before the return
    const handleWordClick = async (word) => {
        setVocabLoading(true);
        setIsNewVocab(false);
        try {
            const vocab = await lookupVocabWord(word);
            if (vocab) {
                setIsNewVocab(!!vocab.is_new); // Only show 'New Vocab Learned' if backend says so
                setVocabModal(vocab);
            }
        } catch (error) {
            console.error("Error looking up vocabulary:", error);
        } finally {
            setVocabLoading(false);
        }
    };

    const setCurrentPageContent = useAppStore((s) => s.setCurrentPageContent);
    const clearCurrentPageContent = useAppStore((s) => s.clearCurrentPageContent);

    useEffect(() => {
        // Set current page content for chat context
        setCurrentPageContent({
            type: "exercise",
            blockId,
            exerciseBlock: current,
            answers,
            evaluation,
            submitted,
            isComplete,
            stage
        });
        return () => {
            clearCurrentPageContent();
        };
    }, [current, answers, evaluation, submitted, isComplete, stage, blockId, setCurrentPageContent, clearCurrentPageContent]);

    // Remove debugStatus and showDebugStatus state

    const [showDebugModal, setShowDebugModal] = useState(false);

    const handleDebug = async () => {
        // Print all feedback-related variables to the console
        console.log("[DEBUG] evaluation:", evaluation);
        console.log("[DEBUG] enhancedResults:", enhancedResults);
        console.log("[DEBUG] submissionStatus:", submissionStatus);
        console.log("[DEBUG] feedbackTimeout:", feedbackTimeout);
        console.log("[DEBUG] submitted:", submitted);
        console.log("[DEBUG] loading:", loading);
        setShowDebugModal(true);
    };

    const debugEnabled = useAppStore((s) => s.debugEnabled);

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
        <div style={{ position: 'relative' }}>
            {showDebugModal && (
                <div style={{ position: 'fixed', top: 16, right: 16, zIndex: 1000, minWidth: 260, maxWidth: 340 }} className="bg-gray-900 text-white rounded shadow-lg p-4 border border-blue-600">
                    <div className="flex justify-between items-center mb-2">
                        <h2 className="text-base font-bold">Frontend Feedback Debug</h2>
                        <button
                            className="ml-2 px-2 py-1 bg-blue-700 text-white rounded hover:bg-blue-800 text-xs"
                            onClick={() => setShowDebugModal(false)}
                        >
                            Close
                        </button>
                    </div>
                    <p className="text-xs">See console for all feedback variables.</p>
                </div>
            )}
            {showTimeoutError && (
                <Alert type="error">
                    Feedback is taking too long to load. You can continue, but some feedback may be missing.
                    <button className="ml-4 underline" onClick={() => setShowTimeoutError(false)}>Dismiss</button>
                </Alert>
            )}
            {/* Sticky progress bar directly under header, above Card */}
            {exercises.length > 0 && (
                <div className="sticky top-[64px] z-30 w-full bg-gray-900 dark:bg-gray-900" style={{marginBottom: '1.5rem'}}>
                    <div
                        className={`w-full rounded-full transition-all duration-300 ${
                            exercises.length > 1
                                ? 'cursor-pointer hover:h-4 hover:shadow-md bg-blue-50 dark:bg-blue-900/20 h-3'
                                : 'cursor-default h-2'
                        }`}
                        onClick={exercises.length > 1 ? handleProgressBarClick : undefined}
                        title={exercises.length > 1 ? `Click to jump to exercise (1-${exercises.length})` : 'Progress'}
                                                style={{
                            minHeight: exercises.length > 1 ? '12px' : '8px'
                        }}
                        onMouseDown={(e) => exercises.length > 1}
                        onMouseUp={(e) => exercises.length > 1}
                    >
                        {/* Background track */}
                        <div className="w-full h-full rounded-full bg-gray-200 dark:bg-gray-800 relative">
                            {/* Progress fill */}
                            <div
                                className={`h-full rounded-full transition-all duration-300 ${
                                    submitted
                                        ? 'bg-blue-500 hover:bg-blue-600'
                                        : 'bg-blue-600'
                                }`}
                                style={{
                                    width: submitted
                                        ? `${((currentExerciseIndex + 1) / exercises.length) * 100}%`
                                        : `${(Object.keys(answers).filter(k => answers[k] && answers[k].trim().length > 0).length / exercises.length) * 100}%`
                                }}
                            ></div>


                        </div>
                    </div>



                    {/* Exercise navigation dots - always visible when multiple exercises */}
                    {exercises.length > 1 && (
                        <div className="flex justify-center items-center gap-2 mt-2">
                            {exercises.map((_, index) => {
                                const hasNewFeedback = exercisesWithNewFeedback.has(index);
                                const isCurrent = index === currentExerciseIndex;
                                const isIncorrect = submitted && evaluation[exercises[index]?.id] && !evaluation[exercises[index]?.id].is_correct;
                                const isLoading = submitted && evaluation[exercises[index]?.id] && evaluation[exercises[index]?.id].loading;



                                return (
                                    <button
                                        key={`${current?.id || 'unknown'}-progress-${index}`}
                                        onClick={() => {
                                            goToExercise(index);
                                            // Clear new feedback indicator when visiting
                                            if (hasNewFeedback) {
                                                setExercisesWithNewFeedback(prev => {
                                                    const newSet = new Set(prev);
                                                    newSet.delete(index);
                                                    return newSet;
                                                });
                                            }
                                        }}
                                        className={`w-3 h-3 rounded-full transition-all duration-200 relative ${
                                            isLoading
                                                ? 'bg-blue-500 dark:bg-blue-400'
                                                : isCurrent
                                                ? `border-2 border-blue-500 dark:border-blue-400 ${isIncorrect ? 'bg-red-500 dark:bg-red-400' : submitted ? 'bg-green-500 dark:bg-green-400' : 'bg-gray-300 dark:bg-gray-600'}`
                                                : isIncorrect
                                                ? 'bg-red-500 dark:bg-red-400'
                                                : submitted
                                                ? 'bg-green-500 dark:bg-green-400'
                                                : 'bg-gray-300 dark:bg-gray-600'
                                        }`}
                                        style={{
                                            transform: isLoading ? 'rotate(0deg)' : 'none',
                                            animation: isLoading ? 'spin 1s linear infinite' : 'none'
                                        }}
                                        title={`Exercise ${index + 1}${hasNewFeedback ? ' - New feedback available!' : ''}${isIncorrect ? ' - Incorrect answer' : ''}${isLoading ? ' - Loading feedback...' : ''}`}
                                    />
                                );
                            })}
                        </div>
                    )}
                </div>
            )}
            <Card className="space-y-4 pb-20">

                {current.title && (
                    <>
                        <h3 className="text-xl font-semibold">{current.title}</h3>
                    </>
                )}
                {instructions && !submitted && <p>{instructions}</p>}
                {/* Always show block ID under instructions, even if no title */}
                {debugEnabled && (
                    <div className="text-xs text-gray-400 font-mono mt-1">
                        Block ID: {current?.id || blockId}
                    </div>
                )}


                                                                        {/* Current Exercise Display */}
                {exercises.length > 0 && (
                    <div className="space-y-6 relative">
                        {/* Navigation tap areas */}
                        {submitted && exercises.length > 1 && (
                            <>
                                {currentExerciseIndex > 0 && (
                                    <div
                                        className="absolute left-0 top-0 bottom-0 w-1/3 z-10 cursor-pointer"
                                        onClick={() => goToPreviousExercise()}
                                        title="Previous exercise"
                                    />
                                )}
                                {currentExerciseIndex < exercises.length - 1 && (
                                    <div
                                        className="absolute right-0 top-0 bottom-0 w-1/3 z-10 cursor-pointer"
                                        onClick={() => goToNextExercise()}
                                        title="Next exercise"
                                    />
                                )}
                            </>
                        )}


                        {(() => {
                            const ex = exercises[currentExerciseIndex];
                            const hasAnswer = answers[ex.id] && answers[ex.id].trim().length > 0;
                            const isIncomplete = !submitted && !hasAnswer;

                            return (
                                <div key={`${current?.id || 'unknown'}-${ex.id}`} className="mb-4">
                                                        {/* Exercise Counter */}


                                    {ex.type === "gap-fill" ? (
                                        <>
                                            <div className="mb-2 font-medium">
                                                {String(ex.question)
                                                    .replace(/\s*\([^)]*\)\s*$/, "") // Remove trailing ( ... )
                                                    .split("___")
                                                    .map((part, idx, arr) => (
                                                        <React.Fragment key={`${current?.id || 'unknown'}-fragment-${idx}`}>
                                                            {renderClickableText(part, handleWordClick)}
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
                                            {ex.options && ex.options.length > 0 && (
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
                                            )}
                                            {isIncomplete && (
                                                null
                                            )}
                                        </>
                                    ) : (
                                        <>
                                            <label className="block mb-2 font-medium">{renderClickableText(ex.question, handleWordClick)}</label>
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

                                    {submitted &&
                                     (currentExerciseIndex === 0 ? evaluation[ex.id] !== undefined : allPreviousFeedbackLoaded(currentExerciseIndex)) &&
                                     evaluation[ex.id] !== undefined && (
                                        <div className="mt-2">
                                            <FeedbackBlock
                                                status={evaluation[ex.id]?.is_correct ? "correct" : "incorrect"}
                                                correct={evaluation[ex.id]?.correct_answer}
                                                alternatives={evaluation[ex.id]?.alternatives || []}
                                                explanation={evaluation[ex.id]?.explanation || ""}
                                                userAnswer={evaluation[ex.id]?.user_answer}
                                                {...(evaluation[ex.id]?.diff && { diff: evaluation[ex.id]?.diff })}
                                                loading={Boolean(evaluation[ex.id]?.loading)}
                                            />
                                        </div>
                                    )}
                                </div>
                            );
                        })()}
                    </div>
                )}

                {/* Navigation Buttons */}
                {submitted && exercises.length > 1 && (
                    <div className="flex justify-between items-center mt-6">
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={goToPreviousExercise}
                            disabled={disablePrev}
                            className="flex items-center gap-2"
                        >
                            ← Previous
                        </Button>

                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={goToNextExercise}
                            disabled={disableNext}
                            className="flex items-center gap-2"
                        >
                            Next →
                        </Button>
                    </div>
                )}


                {/* Removed enhanced results loading banner - basic feedback should always be visible */}

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
            {vocabLoading && (
                <Modal onClose={() => setVocabLoading(false)}>
                    <div className="flex justify-center items-center py-8">
                        <Spinner />
                        <span className="ml-4 text-lg">Loading vocabulary...</span>
                    </div>
                </Modal>
            )}
            {vocabModal && (
                <VocabDetailModal
                    vocab={vocabModal}
                    onClose={() => setVocabModal(null)}
                    title={isNewVocab ? "New Vocab Learned" : "Vocabulary Details"}
                />
            )}
        </div>
    );
}

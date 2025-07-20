import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import useAppStore from "../store/useAppStore";
import Card from "./UI/Card";
import Button from "./UI/Button";
import ProgressRing from "./UI/ProgressRing";
import Spinner from "./UI/Spinner";
import { Container, Title } from "./UI/UI";
import Footer from "./UI/Footer";
import { getAiFeedbackItem, generateAiFeedbackWithProgress, getFeedbackProgress, getFeedbackResult } from "../api";
import AskAiButton from "./AskAiButton";
import AskAiModal from "./AskAiModal";
import { Brain, CheckCircle, Target, BookOpen, Sparkles } from "lucide-react";
import FeedbackBlock from "./FeedbackBlock";

export default function AIFeedbackView() {
    const { feedbackId } = useParams();
    const [feedback, setFeedback] = useState(null);
    const [error, setError] = useState("");
    const [answers, setAnswers] = useState({});
    const [submitted, setSubmitted] = useState(false);
    const navigate = useNavigate();
    const isAdmin = useAppStore((state) => state.isAdmin);
    const addBackgroundActivity = useAppStore((s) => s.addBackgroundActivity);
    const removeBackgroundActivity = useAppStore((s) => s.removeBackgroundActivity);
    const [aiModalOpen, setAiModalOpen] = useState(false);

    // Progress tracking states
    const [generatingFeedback, setGeneratingFeedback] = useState(false);
    const [progressPercentage, setProgressPercentage] = useState(0);
    const [progressStatus, setProgressStatus] = useState("");
    const [progressIcon, setProgressIcon] = useState(Brain);
    const [sessionId, setSessionId] = useState(null);

    // Check if all exercises have answers
    const exercises = feedback?.exercises || [];
    const allExercisesAnswered = exercises.length > 0 && exercises.every(ex => {
        const answer = answers[ex.id];
        return answer && answer.trim().length > 0;
    });

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
        setGeneratingFeedback(true);
        setSubmitted(true);

        // Add background activity for topic memory update
        const topicActivityId = `feedback-topic-${Date.now()}`;
        addBackgroundActivity({
            id: topicActivityId,
            label: "Updating topic memory from feedback...",
            status: "In progress"
        });

        try {
            // Start the feedback generation with progress tracking
            const startResult = await generateAiFeedbackWithProgress({
                answers,
                exercise_block: {
                    exercises: feedback?.exercises || [],
                    lessonId: feedbackId
                }
            });

            if (!startResult.session_id) {
                throw new Error("Failed to start feedback generation");
            }

            setSessionId(startResult.session_id);

            // Poll for progress updates
            const progressInterval = setInterval(async () => {
                try {
                    const progress = await getFeedbackProgress(startResult.session_id);

                    console.log(`[Feedback Progress] ${progress.percentage}% - ${progress.status} - Step: ${progress.step} - Completed: ${progress.completed}`);

                    setProgressPercentage(progress.percentage);
                    setProgressStatus(progress.status);

                    // Set icon based on step
                    const stepIcons = {
                        'init': Brain,
                        'analyzing': Target,
                        'evaluating': Brain,
                        'processing': BookOpen,
                        'fetching_data': BookOpen,
                        'generating_feedback': Sparkles,
                        'updating_progress': Sparkles,
                        'complete': CheckCircle,
                        'error': Brain
                    };

                    const IconComponent = stepIcons[progress.step] || Brain;
                    setProgressIcon(IconComponent);

                    // If complete, get the result
                    if (progress.completed) {
                        console.log(`[Feedback] Progress completed, fetching result...`);
                        clearInterval(progressInterval);

                        if (progress.error) {
                            console.error(`[Feedback] Error in progress: ${progress.error}`);
                            throw new Error(progress.error);
                        }

                        console.log(`[Feedback] Calling getFeedbackResult...`);
                        const startTime = Date.now();
                        const result = await getFeedbackResult(startResult.session_id);
                        const endTime = Date.now();
                        console.log(`[Feedback] getFeedbackResult took ${endTime - startTime}ms`);

                        if (result && result.feedbackPrompt) {
                            console.log(`[Feedback] Setting feedback prompt`);
                            setFeedback((prev) => ({ ...prev, feedbackPrompt: result.feedbackPrompt }));
                        }
                        if (result && Array.isArray(result.results)) {
                            console.log(`[Feedback] Setting exercise results`);
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

                        console.log(`[Feedback] Setting generatingFeedback to false`);
                        setGeneratingFeedback(false);

                        // Remove background activity after completion
                        setTimeout(() => removeBackgroundActivity(topicActivityId), 1200);
                    }
                } catch (err) {
                    console.error("Progress polling failed:", err);
                    clearInterval(progressInterval);
                    setGeneratingFeedback(false);

                    // Remove background activity on error
                    setTimeout(() => removeBackgroundActivity(topicActivityId), 1200);
                }
            }, 200); // Poll every 200ms

        } catch (err) {
            console.error("Failed to generate AI feedback", err);
            setGeneratingFeedback(false);

            // Remove background activity on error
            setTimeout(() => removeBackgroundActivity(topicActivityId), 1200);
        }
    };

    return (
        <div className="min-h-screen flex flex-col bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white">
            <main className="flex-1 pb-20">
                <Container
                    bottom={
                        <Button variant="link" type="button" onClick={() => navigate("/ai-feedback")}>⬅ Back to AI Feedback</Button>
                    }
                >
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
                                    {!submitted && exercises.length > 0 && (
                                        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                                            <div className="flex items-center justify-between">
                                                <span className="text-blue-700 dark:text-blue-300 text-sm font-medium">
                                                    Progress: {Object.keys(answers).filter(k => answers[k] && answers[k].trim().length > 0).length} of {exercises.length} exercises completed
                                                </span>
                                                <div className="w-24 bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                                                    <div
                                                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                                        style={{
                                                            width: `${(Object.keys(answers).filter(k => answers[k] && answers[k].trim().length > 0).length / exercises.length) * 100}%`
                                                        }}
                                                    ></div>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {feedback.exercises.map((ex, idx) => {
                                        const hasAnswer = answers[ex.id] && answers[ex.id].trim().length > 0;
                                        const isIncomplete = !submitted && !hasAnswer;

                                        return (
                                            <div key={ex.id} className={`mb-4 ${isIncomplete ? 'border-l-4 border-orange-400 pl-4' : ''}`}>
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
                                                        {isIncomplete && (
                                                            <p className="text-orange-600 dark:text-orange-400 text-sm mt-2">
                                                                ⚠️ Please select an answer
                                                            </p>
                                                        )}
                                                    </>
                                                ) : (
                                                    <>
                                                        <label className="block mb-2 font-medium">{ex.question}</label>
                                                        <input
                                                            type="text"
                                                            className={`border rounded p-2 w-full ${isIncomplete ? 'border-orange-400 focus:border-orange-500' : ''}`}
                                                            value={answers[ex.id] || ""}
                                                            onChange={(e) => handleSelect(ex.id, e.target.value)}
                                                            disabled={submitted}
                                                            placeholder="Your answer"
                                                        />
                                                        {isIncomplete && (
                                                            <p className="text-orange-600 dark:text-orange-400 text-sm mt-2">
                                                                ⚠️ Please enter your answer
                                                            </p>
                                                        )}
                                                    </>
                                                )}
                                                {submitted && feedback.feedbackBlocks && feedback.feedbackBlocks[idx] && (
                                                    <div className="mt-2">
                                                        <FeedbackBlock
                                                            {...feedback.feedbackBlocks[idx]}
                                                            {...(feedback.feedbackBlocks[idx]?.status !== "correct" && feedback.feedbackBlocks[idx]?.diff ? { diff: feedback.feedbackBlocks[idx].diff } : { diff: undefined })}
                                                            {...(feedback.feedbackBlocks[idx]?.status !== "correct" && feedback.feedbackBlocks[idx]?.correct ? { correct: feedback.feedbackBlocks[idx].correct } : { correct: undefined })}
                                                        />
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                    {!submitted && (
                                        <Button
                                            type="button"
                                            variant="success"
                                            onClick={handleSubmit}
                                            disabled={!allExercisesAnswered}
                                        >
                                            {allExercisesAnswered ? "Submit Answers" : `Complete ${exercises.length - Object.keys(answers).filter(k => answers[k] && answers[k].trim().length > 0).length} more answer${exercises.length - Object.keys(answers).filter(k => answers[k] && answers[k].trim().length > 0).length === 1 ? '' : 's'}`}
                                        </Button>
                                    )}
                                    {generatingFeedback && (
                                        <div className="mt-6 text-center">
                                            <div className="flex justify-center mb-4">
                                                <ProgressRing
                                                    percentage={progressPercentage}
                                                    size={100}
                                                    color={progressPercentage === 99 ? "#10B981" : "#3B82F6"}
                                                />
                                            </div>
                                            <div className="flex items-center justify-center gap-3 mb-3">
                                                {(() => {
                                                    const IconComponent = progressIcon;
                                                    return <IconComponent className="w-5 h-5 text-blue-600 dark:text-blue-400" />;
                                                })()}
                                                <h4 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                                                    {progressStatus}
                                                </h4>
                                            </div>
                                            <p className="text-gray-600 dark:text-gray-400">
                                                {progressPercentage < 99
                                                    ? "We're analyzing your answers and generating personalized feedback."
                                                    : "Your feedback is ready!"
                                                }
                                            </p>
                                            {progressPercentage < 99 && (
                                                <div className="mt-4 flex justify-center">
                                                    <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                                                        <Spinner />
                                                        <span>Please wait...</span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                    {submitted && !generatingFeedback && feedback.feedbackPrompt && (
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
                </Container>
            </main>
            <Footer />
            <AskAiButton onClick={() => setAiModalOpen(true)} />
            {aiModalOpen && (
                <AskAiModal
                    onClose={() => setAiModalOpen(false)}
                    pageContext={{
                        page: "ai-feedback",
                        feedback: feedback?.feedbackPrompt,
                        exercises: feedback?.exercises,
                        answers,
                    }}
                />
            )}
        </div>
    );
}

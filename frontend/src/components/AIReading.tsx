import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen, ArrowLeft } from "lucide-react";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Footer from "./UI/Footer";
import Spinner from "./UI/Spinner";
import ProgressRing from "./UI/ProgressRing";
import { CheckCircle, Brain, Target, Sparkles } from "lucide-react";
import useAppStore from "../store/useAppStore";
import { getReadingExercise, submitReadingAnswers } from "../api";
import FeedbackBlock from "./FeedbackBlock";

function makeSnippet(text: string, answer: string, range = 20): string {
    const index = text.toLowerCase().indexOf(answer.toLowerCase());
    if (index === -1) return "";
    const start = Math.max(0, index - range);
    const end = Math.min(text.length, index + answer.length + range);
    const snippet = text.slice(start, end);
    const escapedAnswer = answer.replace(/([.*+?^${}()|[\]\\])/g, "\\$1");
    const regex = new RegExp(escapedAnswer, "i");
    return snippet.replace(regex, (match) => `<strong class='text-green-600'>${match}</strong>`);
}

function guessCorrectAnswers(text: string, questions: Question[]): Record<string, string> {
    const lowered = text.toLowerCase();
    const map: Record<string, string> = {};
    questions.forEach((q) => {
        const found = q.options.find((opt) => lowered.includes(opt.toLowerCase()));
        if (found) {
            map[q.id] = found;
        }
    });
    return map;
}

interface Question {
    id: string;
    question: string;
    options: string[];
    correctAnswer?: string;
}

interface ReadingData {
    text: string;
    questions: Question[];
    feedbackPrompt?: string;
    vocabHelp?: { word: string; meaning: string }[];
    exercise_id?: string; // Added exercise_id to the interface
}

export default function AIReading() {
    const [style, setStyle] = useState<string>("story");
    const [data, setData] = useState<ReadingData | null>(null);
    const [exerciseId, setExerciseId] = useState<string | null>(null); // Store exercise_id
    const [answers, setAnswers] = useState<Record<string, string>>({});
    const [submitted, setSubmitted] = useState(false);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<Record<string, string>>({});
    const [feedback, setFeedback] = useState<Record<string, string>>({});
    const [progressPercentage, setProgressPercentage] = useState(0);
    const [progressStatus, setProgressStatus] = useState("Initializing...");
    // Change progressIcon state to use React.ElementType
    const [progressIcon, setProgressIcon] = useState<React.ElementType>(Brain);
    const [feedbackBlocks, setFeedbackBlocks] = useState<any[]>([]); // Add this after other useState declarations
    const navigate = useNavigate();
    const darkMode = useAppStore((s) => s.darkMode);
    const addBackgroundActivity = useAppStore((s) => s.addBackgroundActivity);
    const updateBackgroundActivity = useAppStore((s) => s.updateBackgroundActivity);
    const removeBackgroundActivity = useAppStore((s) => s.removeBackgroundActivity);
    // Add error state for API error
    const [apiError, setApiError] = useState(false);

    const startExercise = async () => {
        setLoading(true);
        setAnswers({});
        setResults({});
        setFeedback({});
        setSubmitted(false);
        setProgressPercentage(0);
        setProgressStatus("Initializing...");
        setProgressIcon(Brain);
        let progressInterval: any;
        const progressSteps = [
            { percentage: 15, status: "Analyzing your reading level...", icon: Target },
            { percentage: 35, status: "Reviewing your vocabulary...", icon: BookOpen },
            { percentage: 55, status: "Identifying weak areas...", icon: Brain },
            { percentage: 75, status: "Generating reading exercise...", icon: Sparkles },
            { percentage: 90, status: "Finalizing your lesson...", icon: Sparkles },
            { percentage: 100, status: "Ready!", icon: CheckCircle }
        ];
        let currentStep = 0;
        progressInterval = setInterval(() => {
            if (currentStep < progressSteps.length) {
                const step = progressSteps[currentStep];
                setProgressPercentage(step.percentage);
                setProgressStatus(step.status);
                setProgressIcon(step.icon);
                currentStep++;
            } else {
                clearInterval(progressInterval);
            }
        }, 800);
        try {
            const d = await getReadingExercise(style);
            setData(d);
            setExerciseId((d as any).exercise_id || null); // Store exercise_id
            setProgressPercentage(100);
            setProgressStatus("Ready!");
            setProgressIcon(CheckCircle);
            setApiError(false);
        } catch {
            setApiError(true);
            setData(null);
            setExerciseId(null);
        } finally {
            setLoading(false);
            clearInterval(progressInterval);
        }
    };

    const handleSelect = (id: string, value: string) => {
        setAnswers((prev) => ({ ...prev, [id]: value }));
    };

    const handleSubmit = async () => {
        if (!data || !exerciseId) return;
        setLoading(true);
        setSubmitted(true);
        // Add background activity for saving vocab/memory
        const activityId = `reading-save-${Date.now()}`;
        addBackgroundActivity({ id: activityId, label: "Saving vocab and updating memory...", status: "In progress" });
        try {
            // Only send answers and exercise_id
            const result = await submitReadingAnswers(answers, exerciseId as any);
            console.log("Reading submit result:", result);
            let map: Record<string, string> = {};
            if (result?.results) {
                result.results.forEach((r: { id: string; correct_answer: string }) => {
                    if (r.correct_answer) {
                        map[r.id] = r.correct_answer;
                    }
                });
            }
            // Store feedbackBlocks if present
            if (result && result.feedbackBlocks) {
                setFeedbackBlocks(result.feedbackBlocks);
            } else {
                setFeedbackBlocks([]);
            }
            if (Object.keys(map).length === 0) {
                map = guessCorrectAnswers(data.text, data.questions);
            }
            setResults(map);
            const fb: Record<string, string> = {};
            data.questions.forEach((q) => {
                const ans = map[q.id];
                if (ans) {
                    fb[q.id] = makeSnippet(data.text, ans);
                }
            });
            setFeedback(fb);
            updateBackgroundActivity(activityId, { status: "Done" });
            setTimeout(() => removeBackgroundActivity(activityId), 1200);
        } catch (err) {
            console.error("Reading submit error:", err);
            updateBackgroundActivity(activityId, { status: "Error" });
            setTimeout(() => removeBackgroundActivity(activityId), 1200);
            setFeedbackBlocks([]); // Clear on error
        } finally {
            setLoading(false);
        }
    };

    // Check if all questions have answers
    const allQuestionsAnswered = (
        data &&
        typeof data === "object" &&
        Array.isArray((data as any).questions) &&
        (data as any).questions.length > 0 &&
        (data as any).questions.every((q: any) => {
            const answer = answers[q.id];
            return answer && answer.trim && answer.trim().length > 0;
        })
    );

    if (apiError) {
        return (
            <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
                <Container className="" bottom={null}>
                    <Title className="">
                        <div className="flex items-center gap-2">
                            <BookOpen className="w-6 h-6" />
                            <span>AI Reading Exercise</span>
                        </div>
                    </Title>
                    <Card className="bg-red-100 text-red-800 text-center p-4">
                        <p>🚨 500: Mistral API Error. Please try again later.</p>
                    </Card>
                </Container>
                <Footer>
                    <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")} className="gap-2">
                        <ArrowLeft className="w-4 h-4" />
                        Back
                    </Button>
                </Footer>
            </div>
        );
    }

    if (!data || typeof data !== "object" || !Array.isArray((data as any).questions)) {
        return (
            <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
                <Container className="" bottom={null}>
                    <Title className="">
                        <div className="flex items-center gap-2">
                            <BookOpen className="w-6 h-6" />
                            <span>AI Reading Exercise</span>
                        </div>
                    </Title>
                    <Card className="space-y-4">
                        <label className="block font-medium">Choose a text type:</label>
                        <select value={style} onChange={(e) => setStyle(e.target.value)} className="border p-2 rounded-md">
                            <option value="story">Story</option>
                            <option value="letter">Letter</option>
                            <option value="news">News</option>
                        </select>
                        <Button onClick={startExercise} variant="primary">Start</Button>
                        {loading && (
                            <div className="text-center py-8">
                                <div className="flex justify-center mb-6">
                                    <ProgressRing
                                        percentage={progressPercentage}
                                        size={120}
                                        color={progressPercentage === 100 ? "#10B981" : "#3B82F6"}
                                    />
                                </div>
                                <div className="flex items-center justify-center gap-3 mb-4">
                                    {React.createElement(progressIcon, { className: "w-6 h-6 text-blue-600 dark:text-blue-400" })}
                                    <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                                        {progressStatus}
                                    </h3>
                                </div>
                                <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                                    {progressPercentage < 100
                                        ? "We're crafting a personalized reading exercise for you."
                                        : "Your reading exercise is ready!"}
                                </p>
                                {progressPercentage < 100 && (
                                    <div className="mt-6 flex justify-center">
                                        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                                            <Spinner />
                                            <span>Please wait...</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </Card>
                </Container>
                <Footer>
                    <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")} className="gap-2">
                        <ArrowLeft className="w-4 h-4" />
                        Back
                    </Button>
                </Footer>
            </div>
        );
    }

    return (
        <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
            {/* Sticky progress bar under header */}
            {data && data.questions.length > 0 && !submitted && (
                <div className="sticky top-16 z-30 w-full bg-white dark:bg-gray-900" style={{marginBottom: '1.5rem'}}>
                    <div className="w-full h-2 rounded-full bg-gray-200 dark:bg-gray-800">
                        <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{
                                width: `${(Object.keys(answers).filter(k => answers[k] && answers[k].trim && answers[k].trim().length > 0).length / data.questions.length) * 100}%`
                            }}
                        />
                    </div>
                </div>
            )}
            <Container className="" bottom={null}>
                <Title className="">
                    <div className="flex items-center gap-2">
                        <BookOpen className="w-6 h-6" />
                        <span>Reading Exercise</span>
                    </div>
                </Title>
                <Card className="space-y-4">
                    {data.text.split(/\n\n+/).map((para, idx) => (
                        <p key={idx} className="mb-3 whitespace-pre-line">{para}</p>
                    ))}
                    {data.questions.map((q, idx) => (
                        <div key={q.id} className="space-y-2">
                            <p className="font-medium">{q.question}</p>
                            {q.options.map((opt) => {
                                const isCorrect = results[q.id] === opt;
                                const isSelected = answers[q.id] === opt;
                                let variant = "secondary";
                                if (!submitted) {
                                    variant = isSelected ? "primary" : "secondary";
                                } else {
                                    if (isCorrect) variant = "successBright";
                                    else if (isSelected) variant = "danger";
                                }
                                return (
                                    <Button key={opt} type="button" variant={variant} onClick={() => handleSelect(q.id, opt)} disabled={submitted}>
                                        {opt}
                                    </Button>
                                );
                            })}
                            {submitted && (feedbackBlocks && feedbackBlocks[idx]) && (
                                <div className="mt-2">
                                    <FeedbackBlock {...feedbackBlocks[idx]} />
                                </div>
                            )}
                        </div>
                    ))}
                    {submitted && data.feedbackPrompt && (
                        <Card className="bg-blue-50 dark:bg-blue-900 text-blue-900 dark:text-blue-100 p-4 mt-6">
                            <div className="font-semibold mb-2">AI Feedback</div>
                            <div>{data.feedbackPrompt}</div>
                        </Card>
                    )}
                    {submitted && loading && (
                        <div className="flex flex-col items-center gap-2">
                            <Spinner />
                            <p>AI is thinking...</p>
                        </div>
                    )}
                </Card>
            </Container>
            <Footer>
                {!submitted && (
                    <Button onClick={handleSubmit} variant="success" disabled={!allQuestionsAnswered} className="w-full max-w-xs mx-auto">
                        Submit Answers
                    </Button>
                )}
                <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")} className="gap-2">
                    <ArrowLeft className="w-4 h-4" />
                    Back
                </Button>
            </Footer>
        </div>
    );
}

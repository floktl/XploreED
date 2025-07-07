import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen, ArrowLeft } from "lucide-react";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Footer from "./UI/Footer";
import Spinner from "./UI/Spinner";
import useAppStore from "../store/useAppStore";
import { getReadingExercise, submitReadingAnswers } from "../api";

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
}

export default function AIReading() {
    const [style, setStyle] = useState<string>("story");
    const [data, setData] = useState<ReadingData | null>(null);
    const [answers, setAnswers] = useState<Record<string, string>>({});
    const [submitted, setSubmitted] = useState(false);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<Record<string, string>>({});
    const [feedback, setFeedback] = useState<Record<string, string>>({});
    const navigate = useNavigate();
    const darkMode = useAppStore((s) => s.darkMode);

    const startExercise = async () => {
        setLoading(true);
        setAnswers({});
        setResults({});
        setFeedback({});
        setSubmitted(false);
        try {
            const d = await getReadingExercise(style);
            setData(d);
        } catch {
            setData("API_ERROR_500" as any);
        } finally {
            setLoading(false);
        }
    };

    const handleSelect = (id: string, value: string) => {
        setAnswers((prev) => ({ ...prev, [id]: value }));
    };

    const handleSubmit = async () => {
        if (!data) return;
        setLoading(true);
        setSubmitted(true);
        try {
            const result = await submitReadingAnswers(answers, data);
            let map: Record<string, string> = {};
            if (result?.results) {
                result.results.forEach((r: { id: string; correct_answer: string }) => {
                    if (r.correct_answer) {
                        map[r.id] = r.correct_answer;
                    }
                });
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
        } catch {
            // ignore
        } finally {
            setLoading(false);
        }
    };

    if (data === "API_ERROR_500") {
        return (
            <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
                <Container >
                    <Title>
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

    if (!data) {
        return (
            <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
                <Container >
                    <Title>
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
                        {loading && <Spinner />}
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
            <Container
                bottom={
                    <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")} className="gap-2">
                        <ArrowLeft className="w-4 h-4" />
                        Back
                    </Button>
                }
            >
                <Title>
                    <div className="flex items-center gap-2">
                        <BookOpen className="w-6 h-6" />
                        <span>Reading Exercise</span>
                    </div>
                </Title>
                <Card className="space-y-4">
                    <p>{data.text}</p>
                    {data.questions.map((q) => (
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
                            {submitted && feedback[q.id] && (
                                <p className="text-sm" dangerouslySetInnerHTML={{ __html: `Find it here: ...${feedback[q.id]}...` }} />
                            )}
                        </div>
                    ))}
                    {!submitted && (
                        <Button onClick={handleSubmit} variant="success">
                            Submit Answers
                        </Button>
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
                <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")} className="gap-2">
                    <ArrowLeft className="w-4 h-4" />
                    Back
                </Button>
            </Footer>
        </div>
    );
}

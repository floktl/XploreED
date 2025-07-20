import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AIExerciseBlock from "./AIExerciseBlock";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Footer from "./UI/Footer";
import Spinner from "./UI/Spinner";
import { CheckCircle, XCircle } from "lucide-react";
import useAppStore from "../store/useAppStore";
import { getProgressTest, submitProgressTest } from "../api";

interface TestData {
    sentence: string;
    scrambled: string[];
    exercise_block: any;
    reading: { text: string; questions: { id: string; question: string; options: string[]; correctAnswer?: string }[] };
    english: string;
}

export default function LevelUpTest() {
    const [data, setData] = useState<TestData | null>(null);
    const [loading, setLoading] = useState(true);
    const [stage, setStage] = useState(0);
    const [aiPassed, setAiPassed] = useState(false);
    const [orderAnswer, setOrderAnswer] = useState("");
    const [translation, setTranslation] = useState("");
    const [readingAns, setReadingAns] = useState<Record<string, string>>({});
    const [result, setResult] = useState<boolean | null>(null);
    const [actions, setActions] = useState<React.ReactNode>(null);
    const navigate = useNavigate();
    const darkMode = useAppStore((s) => s.darkMode);

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            try {
                const d = await getProgressTest();
                setData(d);
            } catch {
                setData(null);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    const handleSubmit = async () => {
        if (!data) return;
        setLoading(true);
        try {
            const payload = {
                sentence: data.sentence,
                english: data.english,
                reading: data.reading,
                answers: {
                    ai_pass: aiPassed,
                    order: orderAnswer,
                    translation: translation,
                    reading: readingAns,
                },
            };
            const res = await submitProgressTest(payload);
            setResult(res.passed);
        } catch {
            setResult(false);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <Spinner />
            </div>
        );
    }

    if (!data) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <Card>Failed to load test.</Card>
            </div>
        );
    }

    if (result !== null) {
        return (
            <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
                <Container className="pb-20"
                    bottom={
                        <Button variant="primary" onClick={() => navigate("/menu")}>Back</Button>
                    }
                >
                    <Title>Progress Test Result</Title>
                    <Card className="text-center py-6 flex items-center justify-center gap-2">
                        {result ? (
                            <>
                                <CheckCircle className="w-5 h-5 text-green-600" />
                                <span>You passed the test!</span>
                            </>
                        ) : (
                            <>
                                <XCircle className="w-5 h-5 text-red-600" />
                                <span>You did not pass.</span>
                            </>
                        )}
                    </Card>
                </Container>
                <Footer>
                    <Button
                        variant="primary"
                        size="sm"
                        className="rounded-full"
                        onClick={() => navigate("/menu")}
                    >
                        Back
                    </Button>
                </Footer>
            </div>
        );
    }

    if (stage === 0) {
        return (
            <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
                <Container className="pb-20">
                    <Title>AI Exercises</Title>
                    <AIExerciseBlock
                        data={data.exercise_block}
                        blockId="progress"
                        onComplete={() => {
                            setAiPassed(true);
                            setStage(1);
                        }}
                        setFooterActions={setActions}
                    />
                </Container>
                <Footer>
                    <div className="flex gap-2">{actions}</div>
                </Footer>
            </div>
        );
    }

    if (stage === 1) {
        return (
            <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
                <Container className="pb-20">
                    <Title>Sentence Ordering</Title>
                    <Card className="space-y-4 p-4">
                        <p className="font-mono">{data.scrambled.join(" ")}</p>
                        <Input
                            value={orderAnswer}
                            onChange={(e) => setOrderAnswer(e.target.value)}
                            placeholder="Type the correct sentence"
                        />
                    </Card>
                </Container>
                <Footer>
                    <div className="flex gap-2">
                        {actions}
                        <Button
                            variant="primary"
                            size="sm"
                            className="rounded-full"
                            onClick={() => setStage(2)}
                        >
                            Next
                        </Button>
                    </div>
                </Footer>
            </div>
        );
    }

    if (stage === 2) {
        return (
            <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
                <Container className="pb-20">
                    <Title>Translate</Title>
                    <Card className="space-y-4 p-4">
                        <p>{data.english}</p>
                        <Input
                            value={translation}
                            onChange={(e) => setTranslation(e.target.value)}
                            placeholder="German translation"
                        />
                    </Card>
                </Container>
                <Footer>
                    <div className="flex gap-2">
                        {actions}
                        <Button
                            variant="primary"
                            size="sm"
                            className="rounded-full"
                            onClick={() => setStage(3)}
                        >
                            Next
                        </Button>
                    </div>
                </Footer>
            </div>
        );
    }

    return (
        <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
            <Container className="pb-20">
                <Title>Reading Exercise</Title>
                <Card className="space-y-4 p-4">
                    <p>{data.reading.text}</p>
                    {data.reading.questions.map((q) => (
                        <div key={q.id} className="space-y-2">
                            <p className="font-medium">{q.question}</p>
                            {q.options.map((opt) => (
                                <Button
                                    key={opt}
                                    type="button"
                                    variant={readingAns[q.id] === opt ? "primary" : "secondary"}
                                    onClick={() => setReadingAns({ ...readingAns, [q.id]: opt })}
                                >
                                    {opt}
                                </Button>
                            ))}
                        </div>
                    ))}
                </Card>
            </Container>
            <Footer>
                <div className="flex gap-2">
                    {actions}
                    <Button
                        variant="success"
                        size="sm"
                        className="rounded-full"
                        onClick={handleSubmit}
                    >
                        Submit Test
                    </Button>
                </div>
            </Footer>
        </div>
    );
}

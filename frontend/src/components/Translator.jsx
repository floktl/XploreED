import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Input, Title, Container } from "./UI/UI";
import { Rocket, ArrowLeft, PenSquare } from "lucide-react";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Spinner from "./UI/Spinner";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";
import { translateSentence, translateSentenceStream } from "../api";
import PrettyFeedback from "./PrettyFeedback";
import FeedbackBlock from "./FeedbackBlock";


export default function Translator() {
    const [english, setEnglish] = useState("");
    const [feedback, setFeedback] = useState("");
    const [studentInput, setStudentInput] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [feedbackBlock, setFeedbackBlock] = useState(null);

    const username = useAppStore((state) => state.username);
    const setUsername = useAppStore((state) => state.setUsername);
    const darkMode = useAppStore((state) => state.darkMode);
    const isAdmin = useAppStore((state) => state.isAdmin);
    const addBackgroundActivity = useAppStore((s) => s.addBackgroundActivity);
    const removeBackgroundActivity = useAppStore((s) => s.removeBackgroundActivity);
    const navigate = useNavigate();

    useEffect(() => {
        if (isAdmin) {
            navigate("/admin-panel");
            return;
        }

        const storedUsername = localStorage.getItem("username");
        if (!username && storedUsername) {
            setUsername(storedUsername);
        }

        // Redirect if no session or stored username
        if (!username && !storedUsername) {
            navigate("/");
        }
    }, [isAdmin, username, setUsername, navigate]);

    const handleTranslate = async () => {
        setError("");
        setFeedbackBlock(null);

        if (!english.trim() || !studentInput.trim()) {
            setError("⚠️ Please fill out both fields before submitting.");
            return;
        }

        const payload = {
            english: String(english),
            student_input: String(studentInput),
        };

        // Add background activity for topic memory update
        const topicActivityId = `topic-${Date.now()}`;
        addBackgroundActivity({
            id: topicActivityId,
            label: "Updating topic memory...",
            status: "In progress"
        });

        try {
            setLoading(true);

            await translateSentenceStream(payload, (chunk) => {
                // Parse the JSON chunk to get feedbackBlock
                try {
                    const data = JSON.parse(chunk);
                    if (data.feedbackBlock) {
                        setFeedbackBlock(data.feedbackBlock);
                    }
                } catch (e) {
                    console.error("[CLIENT] Failed to parse chunk:", chunk, e);
                    // fallback: ignore
                }
            });

            setTimeout(() => removeBackgroundActivity(topicActivityId), 1200);
        } catch (err) {
            console.error("[CLIENT] Translation request failed:", err);
            setError("Something went wrong. Please try again.");
            setTimeout(() => removeBackgroundActivity(topicActivityId), 1200);
        } finally {
            setLoading(false);
        }
    };

    const handleReset = () => {
        setEnglish("");
        setStudentInput("");
        setFeedback("");
        setFeedbackBlock(null);
        setError("");
    };

    return (
        <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
            <Container className="pb-20">
                <div className="text-center mb-8">
                    <h1 className={`text-3xl font-bold mb-2 ${darkMode ? "text-blue-400" : "text-blue-600"}`}>
                        Translation Practice
                    </h1>
                    <p className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                        Practice translating English to German and get instant feedback
                    </p>
                </div>

                <form
                    className="space-y-6 max-w-2xl mx-auto"
                    onSubmit={(e) => {
                        e.preventDefault();
                        handleTranslate();
                    }}
                >
                    <div className="space-y-2">
                        <label className={`block text-sm font-medium ${darkMode ? "text-gray-200" : "text-gray-700"}`}>
                            English Text to Translate
                        </label>
                        <Input
                            autoFocus
                            placeholder="Enter English word, phrase, or sentence..."
                            value={english}
                            onChange={(e) => setEnglish(e.target.value)}
                            className="w-full"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className={`block text-sm font-medium ${darkMode ? "text-gray-200" : "text-gray-700"}`}>
                            Your German Translation
                        </label>
                        <Input
                            placeholder="Type your German translation here..."
                            value={studentInput}
                            onChange={(e) => setStudentInput(e.target.value)}
                            className="w-full"
                        />
                    </div>

                    {error && <Alert type="warning">{error}</Alert>}
                    {loading && <Spinner />}

                    <div className="flex flex-col sm:flex-row gap-3">
                        <Button variant="primary" className="w-full gap-2" onClick={handleTranslate} disabled={loading}>
                            <Rocket className="w-4 h-4" />
                            {loading ? "Translating..." : "Get Feedback"}
                        </Button>
                    </div>
                </form>

                {feedbackBlock && (
                    <>
                        <Card className="mt-8 max-w-2xl mx-auto">
                            {/* Use FeedbackBlock for feedback rendering */}
                            {feedbackBlock && (
                                <FeedbackBlock
                                    status={feedbackBlock.status}
                                    correct={feedbackBlock.correct}
                                    alternatives={feedbackBlock.alternatives}
                                    explanation={feedbackBlock.explanation}
                                    userAnswer={feedbackBlock.userAnswer}
                                    diff={feedbackBlock.diff}
                                />
                            )}
                        </Card>

                        <div className="mt-6 text-center">
                            <Button variant="secondary" onClick={handleReset}>
                                🆕 New Translation
                            </Button>
                        </div>
                    </>
                )}
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

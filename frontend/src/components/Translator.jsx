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
import { translateSentence } from "../api";


export default function Translator() {
    const [english, setEnglish] = useState("");
    const [german, setGerman] = useState("");
    const [feedback, setFeedback] = useState("");
    const [studentInput, setStudentInput] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const username = useAppStore((state) => state.username);
    const setUsername = useAppStore((state) => state.setUsername);
    const darkMode = useAppStore((state) => state.darkMode);
    const isAdmin = useAppStore((state) => state.isAdmin);
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

        if (!english.trim() || !studentInput.trim()) {
            setError("⚠️ Please fill out both fields before submitting.");
            return;
        }

        const payload = {
            english: String(english),
            student_input: String(studentInput),
        };

        try {
            setLoading(true);
            const data = await translateSentence(payload);
            setGerman(data.german || "");
            setFeedback(data.feedback || "");
        } catch (err) {
            console.error("[CLIENT] Translation request failed:", err);
            setError("Something went wrong. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const handleReset = () => {
        setEnglish("");
        setStudentInput("");
        setGerman("");
        setFeedback("");
        setError("");
    };

    return (
        <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
            <Container>
                <Title>
                    <div className="flex items-center gap-2">
                        <PenSquare className="w-6 h-6" />
                        <span>{username ? `${username}'s` : "Your"} Translation Practice</span>
                    </div>
                </Title>

                <form
                    className="space-y-4"
                    onSubmit={(e) => {
                        e.preventDefault();
                        handleTranslate();
                    }}
                >
                    <Input
                        autoFocus
                        placeholder="Type your English sentence..."
                        value={english}
                        onChange={(e) => setEnglish(e.target.value)}
                    />

                    <Input
                        placeholder="Your German translation"
                        value={studentInput}
                        onChange={(e) => setStudentInput(e.target.value)}
                    />

                    {error && <Alert type="warning">{error}</Alert>}
                    {loading && <Spinner />}

                    <div className="flex flex-col sm:flex-row gap-3 mt-2">
                        <Button variant="primary" className="w-full gap-2" onClick={handleTranslate} disabled={loading}>
                            <Rocket className="w-4 h-4" />
                            {loading ? "Translating..." : "Get Feedback"}
                        </Button>
                    </div>
                </form>

                {german && (
                    <>
                        <Card className="mt-8">
                            <p className={`text-lg font-semibold mb-2 ${darkMode ? "text-gray-100" : "text-blue-800"}`}>
                                🗣️ Correct German:
                            </p>
                            <p className={`mb-3 ${darkMode ? "text-gray-200" : "text-gray-900"}`}>{german}</p>
                            <div
                                className={`text-sm ${darkMode ? "text-gray-300" : "text-gray-700"}`}
                                dangerouslySetInnerHTML={{ __html: feedback }}
                            />
                        </Card>

                        <div className="mt-6 text-center">
                            <Button variant="secondary" onClick={handleReset}>
                                🆕 New Sentence
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

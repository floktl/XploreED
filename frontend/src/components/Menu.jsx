import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
    FileText,
    Target,
    Book,
    Library,
    Bot,
} from "lucide-react";

import Button from "./UI/Button";
import Card from "./UI/Card";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";
import useAppStore from "../store/useAppStore";
import { getUserLevel } from "../api";
import AskAiButton from "./AskAiButton";

export default function Menu() {
    const navigate = useNavigate();
    const username = useAppStore((state) => state.username);
    const setUsername = useAppStore((state) => state.setUsername);
    const darkMode = useAppStore((state) => state.darkMode);
    const isAdmin = useAppStore((state) => state.isAdmin);
    const isLoading = useAppStore((state) => state.isLoading);
    const setCurrentLevel = useAppStore((state) => state.setCurrentLevel);

    useEffect(() => {
        const storedUsername = localStorage.getItem("username");
        if (!username && storedUsername) {
            setUsername(storedUsername);
        }

        const fetchLevel = async () => {
            try {
                const data = await getUserLevel();
                if (data.level !== undefined) setCurrentLevel(data.level);
            } catch (e) {
                console.error("[Menu] failed to load level", e);
            }
        };
        fetchLevel();

        if (!isLoading && !username) {
            navigate("/");
        }

        if (isAdmin) {
            navigate("/admin-panel");
        }
    }, [username, setUsername, isAdmin, isLoading, navigate]);

    return (
        <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
            <Container>

                <Card className="shadow-xl">
                    <div className="flex flex-col gap-4">
                        <Button type="button" variant="primary" onClick={() => navigate("/translate")} className="justify-start gap-3">
                            <FileText className="w-5 h-5" />
                            Translation Practice
                        </Button>

                        <Button type="button" variant="primary" onClick={() => navigate("/level-game")} className="justify-start gap-3">
                            <Target className="w-5 h-5" />
                            Sentence Order Game
                        </Button>

                        <Button type="button" variant="secondary" onClick={() => navigate("/ai-feedback")} className="justify-start gap-3">
                            <Bot className="w-5 h-5" />
                            AI Training Exercises
                        </Button>

                        <Button type="button" variant="secondary" onClick={() => navigate("/reading-exercise")} className="justify-start gap-3">
                            <Book className="w-5 h-5" />
                            AI Reading Exercise
                        </Button>

                        <Button type="button" variant="secondary" onClick={() => navigate("/lessons")} className="justify-start gap-3">
                            <Library className="w-5 h-5" />
                            {username ? `${username}'s Lessons` : "Your Lessons"}
                        </Button>

                        <Button type="button" variant="secondary" onClick={() => navigate("/weakness-lesson")} className="justify-start gap-3">
                            <Bot className="w-5 h-5" />
                            AI Weakness Lesson
                        </Button>

                        <Button type="button" variant="ghost" onClick={() => navigate("/progress-test-demo")} className="justify-start gap-3">
                            <Target className="w-5 h-5" />
                            Progress Bar Test
                        </Button>

                    </div>
                </Card>
            </Container>
            <AskAiButton />
            <Footer />
        </div>
    );
}

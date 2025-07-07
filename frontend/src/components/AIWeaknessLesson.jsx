import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import useAppStore from "../store/useAppStore";
import { getWeaknessLesson } from "../api";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";

export default function AIWeaknessLesson() {
    const [html, setHtml] = useState("");
    const [error, setError] = useState("");
    const navigate = useNavigate();
    const username = useAppStore((state) => state.username);
    const setUsername = useAppStore((state) => state.setUsername);
    const darkMode = useAppStore((state) => state.darkMode);
    const isAdmin = useAppStore((state) => state.isAdmin);
    const isLoading = useAppStore((state) => state.isLoading);

    useEffect(() => {
        const stored = localStorage.getItem("username");
        if (!username && stored) {
            setUsername(stored);
        }
        if (!isLoading && (!username || isAdmin)) {
            navigate(isAdmin ? "/admin-panel" : "/");
        }
    }, [username, isAdmin, isLoading, navigate, setUsername]);

    useEffect(() => {
        getWeaknessLesson()
            .then(setHtml)
            .catch((err) => {
                console.error("Failed to load lesson", err);
                setError("🚨 500: Mistral API Error. Please try again later.");
            });
    }, []);

    return (
        <div
            className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"
                }`}
        >
            <Container >
                <Title>🤖 Personalized Lesson</Title>
                {error ? (
                    <p className="text-red-600">{error}</p>
                ) : (
                    <Card>
                        <div dangerouslySetInnerHTML={{ __html: html }} />
                    </Card>
                )}
            </Container>
            <Footer>
                <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")} className="gap-2">
                    <ArrowLeft className="w-4 h-4" />
                    Back to Menu
                </Button>
            </Footer>
        </div>
    );
}

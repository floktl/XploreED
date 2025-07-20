import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import useAppStore from "../store/useAppStore";
import { getWeaknessLesson } from "../api";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";
import Spinner from "./UI/Spinner";
import ProgressRing from "./UI/ProgressRing";
import { CheckCircle, Brain, BookOpen, Target, Sparkles } from "lucide-react";

export default function AIWeaknessLesson() {
    const [html, setHtml] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(true);
    const [progressPercentage, setProgressPercentage] = useState(0);
    const [progressStatus, setProgressStatus] = useState("Initializing...");
    const [progressIcon, setProgressIcon] = useState(Brain);
    const navigate = useNavigate();
    const username = useAppStore((state) => state.username);
    const setUsername = useAppStore((state) => state.setUsername);
    const darkMode = useAppStore((state) => state.darkMode);
    const isAdmin = useAppStore((state) => state.isAdmin);
    const isLoading = useAppStore((state) => state.isLoading);
    const addBackgroundActivity = useAppStore((s) => s.addBackgroundActivity);
    const removeBackgroundActivity = useAppStore((s) => s.removeBackgroundActivity);

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
        let isMounted = true;
        let progressInterval;
        const progressSteps = [
            { percentage: 15, status: "Analyzing your weaknesses...", icon: Target },
            { percentage: 35, status: "Reviewing your past answers...", icon: BookOpen },
            { percentage: 55, status: "Identifying weak topics...", icon: Brain },
            { percentage: 75, status: "Generating personalized lesson...", icon: Sparkles },
            { percentage: 90, status: "Finalizing your lesson...", icon: Sparkles },
            { percentage: 99, status: "Ready!", icon: CheckCircle }
        ];
        let currentStep = 0;
        progressInterval = setInterval(() => {
            if (currentStep < progressSteps.length) {
                const step = progressSteps[currentStep];
                setProgressPercentage(step.percentage);
                setProgressStatus(step.status);
                setProgressIcon(() => step.icon);
                currentStep++;
            } else {
                clearInterval(progressInterval);
            }
        }, 800);
        getWeaknessLesson()
            .then((data) => {
                if (isMounted) {
                    setHtml(data);
                    setLoading(false);
                    setProgressPercentage(99);
                    setProgressStatus("Ready!");
                    setProgressIcon(() => CheckCircle);

                    // Add background activity for topic memory update
                    const topicActivityId = `weakness-topic-${Date.now()}`;
                    addBackgroundActivity({
                        id: topicActivityId,
                        label: "Updating topic memory from lesson...",
                        status: "In progress"
                    });

                    // Remove background activity after a delay
                    setTimeout(() => removeBackgroundActivity(topicActivityId), 1200);
                }
            })
            .catch((err) => {
                console.error("Failed to load lesson", err);
                setError("🚨 500: Mistral API Error. Please try again later.");
                setLoading(false);
                const topicActivityId = `weakness-topic-${Date.now()}`;
                addBackgroundActivity({
                    id: topicActivityId,
                    label: "Updating topic memory from lesson...",
                    status: "In progress"
                });
                setTimeout(() => removeBackgroundActivity(topicActivityId), 1200);
            })
            .finally(() => {
                clearInterval(progressInterval);
            });
        return () => {
            isMounted = false;
            clearInterval(progressInterval);
        };
    }, []);

    return (
        <div
            className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"
                }`}
        >
            <Container >
                <Title>Personalized Lesson</Title>
                {loading ? (
                    <Card className="text-center py-8">
                        <div className="flex justify-center mb-6">
                            <ProgressRing
                                percentage={progressPercentage}
                                size={120}
                                color={progressPercentage === 99 ? "#10B981" : "#3B82F6"}
                            />
                        </div>
                        <div className="flex items-center justify-center gap-3 mb-4">
                            {React.createElement(progressIcon, { className: "w-6 h-6 text-blue-600 dark:text-blue-400" })}
                            <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                                {progressStatus}
                            </h3>
                        </div>
                        <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                            {progressPercentage < 99
                                ? "We're crafting a personalized lesson based on your weaknesses."
                                : "Your personalized lesson is ready!"}
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
                ) : error ? (
                    <p className="text-red-600">{error}</p>
                ) : (
                    <Card>
                       <div className="lesson-content prose dark:prose-invert" dangerouslySetInnerHTML={{ __html: html }} />
                    </Card>
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

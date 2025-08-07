import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Button from "./UI/Button";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";
import useAppStore from "../store/useAppStore";
import AIExerciseBlock from "./AIExerciseBlock";
import { getAiExercises } from "../api";

export default function AIFeedback() {
    const navigate = useNavigate();
    const darkMode = useAppStore((state) => state.darkMode);
    const username = useAppStore((state) => state.username);
    const isLoading = useAppStore((state) => state.isLoading);
    const isAdmin = useAppStore((state) => state.isAdmin);
    const [actions, setActions] = useState(null);
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [exerciseTitle, setExerciseTitle] = useState(`${username}'s AI Exercises`);

    useEffect(() => {
        if (!isLoading && (!username || isAdmin)) {
            navigate(isAdmin ? "/admin-panel" : "/");
        }
    }, [username, isLoading, isAdmin, navigate]);

    const handleExerciseDataChange = (exerciseData) => {
        if (exerciseData && exerciseData.title) {
            setExerciseTitle(exerciseData.title);
        }
    };

    return (
        <div className={`min-h-screen flex flex-col ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
            <main className="flex-1 pb-20">
                <Container>
                    <AIExerciseBlock
                        fetchExercisesFn={getAiExercises}
                        setFooterActions={setActions}
                        onSubmissionChange={setIsSubmitted}
                        onExerciseDataChange={handleExerciseDataChange}
                    />
                </Container>
            </main>
            <Footer>
                <div className="flex gap-2">
                    <Button
                        size="sm"
                        variant="ghost"
                        type="button"
                        onClick={() => navigate("/menu")}
                        className="gap-2 rounded-full"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back
                    </Button>
                    {actions}
                </div>
            </Footer>
        </div>
    );
}

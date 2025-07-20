import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Button from "./UI/Button";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";
import useAppStore from "../store/useAppStore";
import AIExerciseBlock from "./AIExerciseBlock";
import { getTrainingExercises } from "../api";

export default function AIFeedback() {
    const navigate = useNavigate();
    const darkMode = useAppStore((state) => state.darkMode);
    const username = useAppStore((state) => state.username);
    const isLoading = useAppStore((state) => state.isLoading);
    const isAdmin = useAppStore((state) => state.isAdmin);
    const [actions, setActions] = useState(null);
    const [isSubmitted, setIsSubmitted] = useState(false);

    useEffect(() => {
        if (!isLoading && (!username || isAdmin)) {
            navigate(isAdmin ? "/admin-panel" : "/");
        }
    }, [username, isLoading, isAdmin, navigate]);


    return (
        <div
            className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"
                }`}
        >
            <Container>
                <Title>{username}'s AI {isSubmitted ? 'Feedback' : 'Exercises'}</Title>
                <AIExerciseBlock
                    blockId="training"
                    fetchExercisesFn={getTrainingExercises}
                    setFooterActions={setActions}
                    onSubmissionChange={setIsSubmitted}
                />
            </Container>
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

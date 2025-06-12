import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
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

  useEffect(() => {
    if (!isLoading && (!username || isAdmin)) {
      navigate(isAdmin ? "/admin-panel" : "/");
    }
  }, [username, isLoading, isAdmin, navigate]);


  return (
    <div
      className={`relative min-h-screen pb-20 ${
        darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"
      }`}
    >
      <Container>
        <Title>🤖 {username}'s AI Lessons</Title>
        <p
          className={`text-center mb-6 ${
            darkMode ? "text-gray-300" : "text-gray-600"
          }`}
        >
          Practice with our AI generated exercises
        </p>
        <AIExerciseBlock fetchExercisesFn={getTrainingExercises} />
        <div className="mt-6 text-center">
          <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")}>
            🔙 Back to Menu
          </Button>
        </div>
      </Container>
      <Footer />
    </div>
  );
}

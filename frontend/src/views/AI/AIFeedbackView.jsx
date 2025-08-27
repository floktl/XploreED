import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import useAppStore from "../store/useAppStore";
import {
  AIFeedbackContent,
  AIFeedbackFooter
} from "../components/AIFeedback";

export default function AIFeedbackView() {
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
        <AIFeedbackContent
          setActions={setActions}
          setIsSubmitted={setIsSubmitted}
          onExerciseDataChange={handleExerciseDataChange}
        />
      </main>
      <AIFeedbackFooter onNavigate={navigate} actions={actions} />
    </div>
  );
}

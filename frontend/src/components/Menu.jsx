import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  FileText,
  Target,
  Book,
  Library,
  Bot,
  BarChart3,
  BrainCircuit,
} from "lucide-react";

import Button from "./UI/Button";
import Card from "./UI/Card";
import Badge from "./UI/Badge";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";
import useAppStore from "../store/useAppStore";

export default function Menu() {
  const navigate = useNavigate();
  const username = useAppStore((state) => state.username);
  const setUsername = useAppStore((state) => state.setUsername);
  const darkMode = useAppStore((state) => state.darkMode);
  const isAdmin = useAppStore((state) => state.isAdmin);
  const isLoading = useAppStore((state) => state.isLoading);

  useEffect(() => {
    const storedUsername = localStorage.getItem("username");
    if (!username && storedUsername) {
      setUsername(storedUsername);
    }

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
        <Title className="text-3xl font-bold mb-2">
          Welcome, {username || "User"} <Badge type="default">Student</Badge>
        </Title>

        <p className={`text-center text-sm mb-2 ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
          Current Level: {useAppStore.getState().currentLevel ?? 0}
        </p>

        <p className={`text-center mb-6 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>
          Choose one of the modes below to begin your practice:
        </p>

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

            <Button type="button" variant="primary" onClick={() => navigate("/vocabulary")} className="justify-start gap-3">
              <Book className="w-5 h-5" />
              My Vocabulary
            </Button>

            <Button type="button" variant="secondary" onClick={() => navigate("/lessons")} className="justify-start gap-3">
              <Library className="w-5 h-5" />
              {username ? `${username}'s Lessons` : "Your Lessons"}
            </Button>

            <Button type="button" variant="secondary" onClick={() => navigate("/ai-feedback")} className="justify-start gap-3">
              <Bot className="w-5 h-5" />
              AI Lessons
            </Button>

            <Button type="button" variant="secondary" onClick={() => navigate("/topic-memory")} className="justify-start gap-3">
              <BrainCircuit className="w-5 h-5" />
              Topic Memory
            </Button>

            <Button type="button" variant="secondary" onClick={() => navigate("/profile")} className="justify-start gap-3">
              <BarChart3 className="w-5 h-5" />
              My Progress
            </Button>
          </div>
        </Card>
      </Container>

      <Footer />
    </div>
  );
}

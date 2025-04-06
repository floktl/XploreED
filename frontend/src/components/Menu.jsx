import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
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

  useEffect(() => {
    const storedUsername = localStorage.getItem("username");
    if (!username && storedUsername) {
      setUsername(storedUsername);
    }
  
    if (isAdmin) {
      navigate("/admin-panel");
    }
  }, [username, setUsername, isAdmin, navigate]);
  
  
  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>
          👋 Welcome, {username || "User"}{" "}
          <Badge type="default">Student</Badge>
          <br />
          <span className="text-sm font-normal text-gray-500 dark:text-gray-400">
            Current Level: {useAppStore.getState().currentLevel ?? 0}
          </span>
        </Title>

        <p className={`text-center mb-6 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>
          Choose one of the modes below to begin your practice:
        </p>

        <Card>
          <div className="flex flex-col gap-4">
            <Button onClick={() => navigate("/translate")}>
              📝 Translation Practice
            </Button>

            <Button onClick={() => navigate("/level-game")}>
              🎯 Sentence Order Game
            </Button>

            <Button onClick={() => navigate("/vocabulary")}>
              📖 My Vocabulary
            </Button>

            <Button onClick={() => navigate("/lessons")} type="secondary">
              📚 Flo's Lessons
            </Button>

            <Button onClick={() => navigate("/profile")} type="secondary">
              👤 My Progress
            </Button>
          </div>
        </Card>
      </Container>

      <Footer />
    </div>
  );
}

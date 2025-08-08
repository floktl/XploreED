import React, { useLayoutEffect, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, Target, Book, Library, Bot, BarChart3, Brain } from "lucide-react";

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
  const debugEnabled = useAppStore((state) => state.debugEnabled);
  const setCurrentLevel = useAppStore((state) => state.setCurrentLevel);
  const setCurrentPageContent = useAppStore((s) => s.setCurrentPageContent);
  const clearCurrentPageContent = useAppStore((s) => s.clearCurrentPageContent);
  const setFooterVisible = useAppStore((s) => s.setFooterVisible);

  useLayoutEffect(() => {
    setFooterVisible(false); // No footer on menu
  }, [setFooterVisible]);

  useEffect(() => {
    // If admin, go straight to admin panel and skip student data fetches
    if (isAdmin) {
      navigate("/admin-panel");
      return;
    }
    const storedUsername = localStorage.getItem("username");
    if (!username && storedUsername) {
      setUsername(storedUsername);
    }

    // Only fetch level if we have a username
    if (username && !isLoading) {
      const fetchLevel = async () => {
        try {
          const data = await getUserLevel();
          if (data.level !== undefined) setCurrentLevel(data.level);
        } catch (e) {
          console.error("[Menu] failed to load level", e);
          // If authentication fails, redirect to login
          if (e.message.includes("Failed to fetch user level")) {
            navigate("/");
          }
        }
      };
      fetchLevel();
    }

    if (!isLoading && !username) {
      navigate("/");
    }

    // note: admin handling is done at the start of this effect

    setCurrentPageContent({
      type: "menu",
      description: "This is the main menu of the XplorED app. Users can access translation practice, sentence order games, AI training exercises, AI reading exercises, weakness lessons, and more. Each button navigates to a different learning module.",
      sections: [
        { label: "Translation Practice", path: "/translate", icon: "FileText" },
        ...(debugEnabled ? [{ label: "Sentence Order Game", path: "/level-game", icon: "Target" }] : []),
        { label: "AI Training Exercises", path: "/ai-feedback", icon: "Bot" },
        { label: "AI Reading Exercise", path: "/reading-exercise", icon: "Book" },
        { label: "Weakness Lesson", path: "/weakness-lesson", icon: "Brain" },
        // Add more sections as needed
      ]
    });
    return () => clearCurrentPageContent();
  }, [username, setUsername, isAdmin, isLoading, navigate, setCurrentLevel, setCurrentPageContent, clearCurrentPageContent, setFooterVisible]);

  return (
    <div
      className={`relative min-h-screen pb-20 overflow-hidden flex flex-col ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}
    >
      <Container>
        <Card className="shadow-xl">
          <div className="flex flex-col gap-4">
            <Button
              type="button"
              variant="primary"
              onClick={() => navigate("/translate")}
              className="justify-start gap-3"
            >
              <FileText className="w-5 h-5" />
              Translation Practice
            </Button>
            {debugEnabled && (
              <Button
                type="button"
                variant="primary"
                onClick={() => navigate("/level-game")}
                className="justify-start gap-3"
              >
                <Target className="w-5 h-5" />
                Sentence Order Game
              </Button>
            )}
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate("/ai-feedback")}
              className="justify-start gap-3"
            >
              <Bot className="w-5 h-5" />
              AI Training Exercises
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate("/reading-exercise")}
              className="justify-start gap-3"
            >
              <Book className="w-5 h-5" />
              AI Reading Exercise
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate("/weakness-lesson")}
              className="justify-start gap-3"
            >
              <Brain className="w-5 h-5" />
              Weakness Lesson
            </Button>
            {/* ...rest of the menu... */}
          </div>
        </Card>
      </Container>
      <AskAiButton />
    </div>
  );
}

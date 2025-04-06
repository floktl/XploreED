import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";
import useAppStore from "../store/useAppStore";

export default function Lessons() {
  const [lessons, setLessons] = useState([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const darkMode = useAppStore((state) => state.darkMode);
  const username = useAppStore((state) => state.username) || "anonymous";

  useEffect(() => {
    const fetchLessons = async () => {
      try {
        const res = await fetch(`http://backend:5000/api/lessons?username=${username}`);
        if (!res.ok) throw new Error("Failed to fetch lessons");
        const data = await res.json();
        setLessons(data);
      } catch (err) {
        console.error("[CLIENT] Failed to load lessons:", err);
        setError("❌ Could not load lessons. Please try again later.");
      }
    };

    fetchLessons();
  }, [username]);

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>📚 Your Lessons</Title>
        <p className={`text-center mb-6 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>
          Overview of your past and upcoming lessons
        </p>

        {error && (
          <Alert type="danger">{error}</Alert>
        )}

        {lessons.length === 0 && !error ? (
          <Alert type="info">
            🤓 No lessons yet. Start practicing to track your progress!
          </Alert>
        ) : (
          <div className="flex flex-col gap-4">
            {lessons.map((lesson) => (
              <Card key={lesson.id}>
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-semibold">{lesson.title || `Lesson ${lesson.id + 1}`}</h3>
                    <p className={`text-sm ${lesson.completed ? "text-green-500" : "text-yellow-500"}`}>
                      {lesson.completed ? "✅ Completed" : "⏳ In Progress"}
                    </p>
                    {lesson.last_attempt && (
                      <p className="text-xs text-gray-400">
                        Last Attempt: {new Date(lesson.last_attempt).toLocaleString()}
                      </p>
                    )}
                  </div>
                  <Button
                    type={lesson.completed ? "secondary" : "primary"}
                    onClick={() => navigate(`/lesson/${lesson.id}`)}
                  >
                    {lesson.completed ? "🔁 Review" : "▶️ Continue"}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}

        <div className="mt-6 text-center">
          <Button type="link" onClick={() => navigate("/menu")}>
            ⬅️ Back to Menu
          </Button>
        </div>
      </Container>

      <Footer />
    </div>
  );
}

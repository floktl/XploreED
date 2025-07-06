import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";
import { ArrowLeft } from "lucide-react";
import useAppStore from "../store/useAppStore";
import { getStudentLessons } from "../api";


export default function Lessons() {
  const [lessons, setLessons] = useState([]);
  const [error, setError] = useState("");
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
  useEffect(() => {
    if (!username) return;
  
    const fetchLessons = async () => {
      try {
        const data = await getStudentLessons(); // ✅ use central API helper
        setLessons(data);
      } catch (err) {
        console.error("[CLIENT] Failed to load lessons:", err);
        setError("Could not load lessons. Please try again later.");
      }
    };
  
    fetchLessons();
  }, [username]);
  

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container
        bottom={
          <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")} className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Menu
          </Button>
        }
      >
        <Title>📚 {username}'s Lessons</Title>
        <p className={`text-center mb-6 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>
          Overview of your past and upcoming lessons
        </p>

        {error && <Alert type="danger">{error}</Alert>}

        {lessons.length === 0 && !error ? (
          <Alert type="info">🤓 No lessons yet. Start practicing to track your progress!</Alert>
        ) : (
          <div className="flex flex-col gap-4">
            {(() => {
              const completed = lessons
                .filter((l) => l.completed)
                .sort((a, b) => a.id - b.id);

              const nextUnfinished = lessons
                .filter((l) => !l.completed)
                .sort((a, b) => a.id - b.id)[0];

              const visibleLessons = nextUnfinished
                ? [...completed, nextUnfinished]
                : completed;

              return visibleLessons.map((lesson) => (

                <Card key={lesson.id}>
                  <div className="flex justify-between items-center">
                    <div className="flex justify-start items-baseline w-1/2 min-w-0 overflow-hidden">
                      <h3 className="font-semibold truncate" title={lesson.title}>{lesson.title || `Lesson ${lesson.id + 1}`}</h3>
                      <p className={`text-sm mx-2 flex items-center space-x-1 ${lesson.completed ? "text-green-600" : "text-gray-500"}`}>
                        {lesson.completed ? (
                          <>
                            <span className="text-base">✅</span>
                            <span>Completed</span>
                          </>
                        ) : (
                          <>
                            <span className="text-base">📊</span>
                            <span>{Math.round(lesson.percent_complete || 0)}% Complete</span>
                          </>
                        )}
                      </p>
                      {lesson.last_attempt && (
                        <p className="text-xs text-gray-400">
                          Last Attempt: {new Date(lesson.last_attempt).toLocaleString()}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="secondary"
                      type="button"
                      className="relative overflow-hidden w-1/2"
                      onClick={() => navigate(`/lesson/${lesson.id}`)}
                    >
                      <span className="relative z-10">
                        {lesson.completed ? "🔁 Review" : "▶️ Continue"}
                      </span>
                      {!lesson.completed && (
                        <span
                          className="absolute top-0 left-0 h-full bg-blue-500 opacity-30"
                          style={{ width: `${lesson.percent_complete || 0}%` }}
                        />
                      )}
                    </Button>
                  </div>
                </Card>
              ));
            })()}
          </div>
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

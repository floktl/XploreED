import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import useAppStore from "../store/useAppStore";
import BlockContentRenderer from "./BlockContentRenderer"; 
import Card from "./UI/Card";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";

export default function LessonView() {
  const { lessonId } = useParams();
  const [entries, setEntries] = useState([]);
  const [progress, setProgress] = useState({});
  const [percentComplete, setPercentComplete] = useState(0);
  const [canComplete, setCanComplete] = useState(false);
  const [markedComplete, setMarkedComplete] = useState(false);
  const navigate = useNavigate();
  const isAdmin = useAppStore((state) => state.isAdmin);

  useEffect(() => {
    if (isAdmin) {
      navigate("/admin-panel");
      return;
    }

    const fetchLesson = async () => {
      try {
        const res = await fetch(`http://localhost:5050/api/lesson/${lessonId}`, {
          method: "GET",
          credentials: "include",
        });
        if (!res.ok) throw new Error("Failed to fetch lesson content");
        const data = await res.json();
        setEntries(data);
      } catch (err) {
        console.error("Failed to load lesson content", err);
      }
    };

    const fetchProgress = async () => {
      try {
        const res = await fetch(`http://localhost:5050/api/lesson-progress/${lessonId}`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          setProgress(data);
        }
      } catch (err) {
        console.warn("Could not load progress", err);
      }
    };

    fetchLesson();
    fetchProgress();
  }, [lessonId, isAdmin, navigate]);

  useEffect(() => {
    const total = Object.keys(progress).length;
    const completed = Object.values(progress).filter(Boolean).length;
  
    setPercentComplete(total > 0 ? (completed / total) * 100 : 0);
  
    // allow marking complete if no checkboxes OR all are complete
    setCanComplete(total === 0 || completed === total);
  }, [progress]);
  

  const handleMarkComplete = async () => {
    if (!canComplete) {
      alert("⚠️ Please complete all blocks before marking the lesson as done.");
      return;
    }

    try {
      const res = await fetch("http://localhost:5050/api/lesson-progress-complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ lesson_id: lessonId }),
      });
      if (!res.ok) throw new Error("Failed to mark complete");

      alert("✅ Lesson marked as completed!");
      setMarkedComplete(true);
      navigate("/lessons");
    } catch (err) {
      console.error("❌ Could not mark lesson complete:", err);
      alert("Failed to mark lesson complete.");
    }
  };

  return (
    <div className="min-h-screen pb-20 bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white">
      <Container>
        <Title>📘 Lesson {lessonId}</Title>

        {entries.length > 0 && (
          <div className="mb-6">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Progress: {Math.round(percentComplete)}%
            </p>
            <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded">
              <div
                className="h-2 bg-green-500 rounded"
                style={{ width: `${percentComplete}%` }}
              ></div>
            </div>

            <div className="mt-4 text-right">
              <Button
                variant={markedComplete ? "secondary" : "success"}
                disabled={!canComplete || markedComplete}
                onClick={handleMarkComplete}
              >
                {markedComplete ? "✅ Marked as Completed" : "✅ Mark Lesson as Completed"}
              </Button>
            </div>
          </div>
        )}

        {entries.length === 0 ? (
          <p>No content found.</p>
        ) : (
          <div className="space-y-4">
            {entries.map((entry, i) => (
  <Card key={i}>
    <h3 className="text-xl font-semibold">{entry.title}</h3>
    <p className="text-sm text-gray-500 dark:text-gray-400">
      Added on {new Date(entry.created_at).toLocaleString()}
    </p>
    <BlockContentRenderer
      html={entry.content}
      progress={progress}
      onToggle={async (blockId, completed) => {
        try {
          await fetch("http://localhost:5050/api/lesson-progress", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({
              lesson_id: parseInt(lessonId),
              block_id: blockId,
              completed,
            }),
          });

          setProgress((prev) => ({
            ...prev,
            [blockId]: completed,
          }));
        } catch (err) {
          console.error("❌ Failed to update progress", err);
        }
      }}
    />
  </Card>
))}
          </div>
        )}

        <div className="text-center mt-8">
          <Button variant="link" type="button" onClick={() => navigate("/lessons")}>
            ⬅ Back to Lessons
          </Button>
        </div>
      </Container>
    </div>
  );
}

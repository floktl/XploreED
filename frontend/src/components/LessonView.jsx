import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Card from "./UI/Card";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";

export default function LessonView() {
  const { lessonId } = useParams();
  const [entries, setEntries] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`http://localhost:5050/api/lesson/${lessonId}`)
      .then((res) => res.json())
      .then(setEntries)
      .catch((err) => console.error("Failed to load lesson content", err));
  }, [lessonId]);

  return (
    <div className="min-h-screen pb-20 bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white">
      <Container>
        <Title>📘 Lesson {lessonId}</Title>
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
                <p className="mt-2 whitespace-pre-wrap">{entry.content}</p>
              </Card>
            ))}
          </div>
        )}

        <div className="text-center mt-8">
          <Button type="link" onClick={() => navigate("/lessons")}>
            ⬅ Back to Lessons
          </Button>
        </div>
      </Container>
    </div>
  );
}

import React from "react";
import LessonCard from "./LessonCard";

export default function LessonsList({ lessons }) {
  // Ensure lessons is an array before filtering
  const lessonsArray = Array.isArray(lessons) ? lessons : [];

  const completed = lessonsArray
    .filter((l) => l.completed)
    .sort((a, b) => a.lesson_id - b.lesson_id);

  const nextUnfinished = lessonsArray
    .filter((l) => !l.completed)
    .sort((a, b) => a.lesson_id - b.lesson_id)[0];

  const visibleLessons = nextUnfinished
    ? [...completed, nextUnfinished]
    : completed;

  return (
    <div className="flex flex-col gap-4">
      {visibleLessons.map((lesson) => (
        <LessonCard key={lesson.lesson_id} lesson={lesson} />
      ))}
    </div>
  );
}

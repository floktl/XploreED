import React from "react";

interface ExerciseDetailsProps {
    exercise: { id: number | string; question: string };
    userAnswer: string;
    correctAnswer: string;
}

export default function ExerciseDetails({
    exercise,
    userAnswer,
    correctAnswer
}: ExerciseDetailsProps) {
    return (
        <div className="mb-2">
            <p className="mb-2 text-sm break-words">
                <strong>Question:</strong> {exercise.question}
            </p>
            <p className="mb-1 text-sm break-words">
                <strong>Your answer:</strong> {userAnswer || "(empty)"}
            </p>
            <p className="mb-2 text-sm break-words">
                <strong>AI answer:</strong> {correctAnswer}
            </p>
        </div>
    );
}

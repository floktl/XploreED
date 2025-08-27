import React from "react";
import { Input } from "../../UI/UI";
import Button from "../../UI/Button";
import FeedbackBlock from "../../FeedbackBlock";

function renderClickableText(text, onWordClick) {
    if (!text) return null;
    const parts = text.split(/(\b[\wÄÖÜäöüß]+\b)/g);
    return parts.map((part, i) => {
        if (/^\w+$/u.test(part)) {
            return (
                <span
                    key={i}
                    className="underline decoration-dotted cursor-pointer hover:text-blue-500"
                    onClick={() => onWordClick(part)}
                >
                    {part}
                </span>
            );
        }
        return part;
    });
}

export default function ExerciseItem({
    exercise,
    answers,
    submitted,
    evaluation,
    currentExerciseIndex,
    allPreviousFeedbackLoaded,
    handleSelect,
    handleWordClick,
    isIncomplete
}) {
    const isMultipleChoice = exercise.options && Array.isArray(exercise.options);
    const showFeedback = submitted &&
        (currentExerciseIndex === 0 ? evaluation[exercise.id] !== undefined : allPreviousFeedbackLoaded(currentExerciseIndex)) &&
        evaluation[exercise.id] !== undefined &&
        evaluation[exercise.id].loading === false;

    return (
        <div key={exercise.id} className="mb-6 p-4 border rounded-lg bg-white dark:bg-gray-800">
            <div className="mb-4">
                <h3 className="text-lg font-semibold mb-2">Exercise {exercise.id}</h3>
                {isMultipleChoice ? (
                    <>
                        <label className="block mb-2 font-medium">
                            {renderClickableText(exercise.question, handleWordClick)}
                        </label>
                        <div className="space-y-2">
                            {exercise.options.map((opt, optIndex) => (
                                <Button
                                    key={optIndex}
                                    variant={answers[exercise.id] === opt ? "primary" : "secondary"}
                                    size="sm"
                                    className="w-full justify-start"
                                    onClick={() => handleSelect(exercise.id, opt)}
                                    disabled={submitted}
                                >
                                    {opt}
                                </Button>
                            ))}
                        </div>
                    </>
                ) : (
                    <>
                        <label className="block mb-2 font-medium">
                            {renderClickableText(exercise.question, handleWordClick)}
                        </label>
                        <Input
                            type="text"
                            value={answers[exercise.id] || ""}
                            onChange={(e) => handleSelect(exercise.id, e.target.value)}
                            disabled={submitted}
                            placeholder="Your answer"
                            className={isIncomplete ? 'border-orange-400 focus:border-orange-500' : ''}
                        />
                    </>
                )}

                {showFeedback && (
                    <div className="mt-2">
                        <FeedbackBlock
                            status={evaluation[exercise.id]?.is_correct ? "correct" : "incorrect"}
                            correct={evaluation[exercise.id]?.correct_answer}
                            alternatives={evaluation[exercise.id]?.alternatives || []}
                            explanation={evaluation[exercise.id]?.explanation || ""}
                            userAnswer={evaluation[exercise.id]?.user_answer}
                            {...(evaluation[exercise.id]?.diff && { diff: evaluation[exercise.id]?.diff })}
                            loading={false}
                        />
                    </div>
                )}
            </div>
        </div>
    );
}

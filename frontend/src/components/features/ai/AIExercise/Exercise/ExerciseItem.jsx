import { Input } from "../../../../common/UI/UI";
import Button from "../../../../common/UI/Button";
import FeedbackBlock from "../../../../common/FeedbackBlock/FeedbackBlock";

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
    isIncomplete,
    enhancedResultsLoading,
    currentDetailedFeedbackIndex
}) {
    const isMultipleChoice = exercise.options && Array.isArray(exercise.options);
    const showFeedback = submitted && evaluation[exercise.id] !== undefined;

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

                {/* Debug info - remove this later */}
                {submitted && !showFeedback && (
                    <div className="mt-2 p-2 bg-yellow-100 dark:bg-yellow-900/20 rounded text-xs">
                        Debug: submitted={submitted.toString()},
                        evaluation exists={evaluation[exercise.id] !== undefined ? 'yes' : 'no'},
                        loading={evaluation[exercise.id]?.loading?.toString() || 'undefined'}
                    </div>
                )}

                {/* Loading detailed feedback indicator - only for current exercise being processed */}
                {submitted && enhancedResultsLoading && currentDetailedFeedbackIndex === currentExerciseIndex && (
                    <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg border border-blue-200 dark:border-blue-700">
                        <div className="flex items-center justify-center gap-3">
                            <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-500 border-t-transparent"></div>
                            <div className="text-center">
                                <div className="font-medium text-blue-700 dark:text-blue-300">Loading Detailed Explanation</div>
                                <div className="text-sm text-blue-600 dark:text-blue-400">AI is generating detailed feedback for this question...</div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

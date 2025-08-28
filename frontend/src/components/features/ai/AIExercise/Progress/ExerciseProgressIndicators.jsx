import React from "react";

export default function ExerciseProgressIndicators({
    currentExerciseIndex,
    totalExercises,
    completedExercises = 0,
    evaluation = {},
    onExerciseClick
}) {
    const progressPercentage = totalExercises > 0 ? (completedExercises / totalExercises) * 100 : 0;

    return (
        <div className="mb-6">
            {/* Progress Bar */}
            <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Progress: {completedExercises}/{totalExercises}
                    </span>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {Math.round(progressPercentage)}%
                    </span>
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                    Click on the bar or dots to navigate between exercises
                </div>
                <div
                    className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 cursor-pointer relative"
                    onClick={(e) => {
                        if (onExerciseClick) {
                            const rect = e.currentTarget.getBoundingClientRect();
                            const clickX = e.clientX - rect.left;
                            const percentage = (clickX / rect.width) * 100;
                            const targetIndex = Math.floor((percentage / 100) * totalExercises);
                            const clampedIndex = Math.max(0, Math.min(totalExercises - 1, targetIndex));
                            onExerciseClick(clampedIndex);
                        }
                    }}
                >
                    <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-in-out"
                        style={{ width: `${progressPercentage}%` }}
                    />
                </div>
            </div>

            {/* Question Dots */}
            <div className="flex justify-center space-x-2">
                {Array.from({ length: totalExercises }, (_, index) => {
                    // Get the exercise ID for this index
                    const exerciseId = `ex${index + 1}`;
                    const exerciseEvaluation = evaluation[exerciseId];

                    // Determine dot color based on evaluation status
                    let dotColor = 'bg-gray-300 dark:bg-gray-600'; // Default: not attempted

                    if (exerciseEvaluation) {
                        if (exerciseEvaluation.correct) {
                            dotColor = 'bg-green-500'; // Correct
                        } else {
                            dotColor = 'bg-red-500'; // Incorrect
                        }
                    } else if (index === currentExerciseIndex) {
                        dotColor = 'bg-blue-500'; // Current exercise
                    }

                    return (
                        <div
                            key={index}
                            className={`w-3 h-3 rounded-full transition-all duration-200 cursor-pointer hover:scale-110 ${
                                index === currentExerciseIndex ? 'scale-150' : ''
                            } ${dotColor}`}
                            title={`Question ${index + 1}${exerciseEvaluation ? ` - ${exerciseEvaluation.correct ? 'Correct' : 'Incorrect'}` : ''}`}
                            onClick={() => onExerciseClick && onExerciseClick(index)}
                        />
                    );
                })}
            </div>
        </div>
    );
}

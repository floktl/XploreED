import React from "react";
import Button from "../../UI/Button";

export default function ExerciseNavigation({
    submitted,
    exercises,
    currentExerciseIndex,
    goToPreviousExercise,
    goToNextExercise,
    disablePrev,
    disableNext,
    answers
}) {
    if (!submitted || exercises.length <= 1) return null;

    return (
        <div className="flex justify-between items-center mt-6">
            <Button
                variant="secondary"
                size="sm"
                onClick={goToPreviousExercise}
                disabled={disablePrev}
                className="flex items-center gap-2"
            >
                ← Previous
            </Button>

            <Button
                variant="secondary"
                size="sm"
                onClick={goToNextExercise}
                disabled={disableNext || (!submitted && !(answers[exercises[currentExerciseIndex]?.id] && (typeof answers[exercises[currentExerciseIndex]?.id] === 'string' ? answers[exercises[currentExerciseIndex]?.id].trim().length > 0 : true)))}
                className="flex items-center gap-2"
            >
                Next →
            </Button>
        </div>
    );
}

import Button from "../../../../common/UI/Button";

export default function ExerciseNavigation({
    submitted,
    exercises,
    currentExerciseIndex,
    goToPreviousExercise,
    goToNextExercise,
    disablePrev,
    disableNext,
    answers,
    onExerciseClick
}) {
    if (exercises.length <= 1) return null;

    return (
        <div className="mt-6 space-y-4">
            {/* Exercise-specific navigation buttons */}
            <div className="flex justify-center gap-2">
                {exercises.map((exercise, index) => (
                    <Button
                        key={exercise.id}
                        variant={index === currentExerciseIndex ? "primary" : "secondary"}
                        size="sm"
                        onClick={() => onExerciseClick && onExerciseClick(index)}
                        className="flex items-center gap-2 min-w-[80px]"
                    >
                        {index === currentExerciseIndex ? "●" : "○"} Exercise {index + 1}
                    </Button>
                ))}
            </div>

            {/* Previous/Next navigation */}
            {submitted && (
                <div className="flex justify-between items-center">
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
                        disabled={disableNext}
                        className="flex items-center gap-2"
                    >
                        Next →
                    </Button>
                </div>
            )}
        </div>
    );
}

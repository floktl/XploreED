import React from "react";
import { Container } from "../UI/UI";
import AIExerciseBlock from "../AIExerciseBlock";
import { getAiExercises } from "../../api";

export default function AIFeedbackContent({
  setActions,
  setIsSubmitted,
  onExerciseDataChange
}) {
  return (
    <Container>
      <AIExerciseBlock
        fetchExercisesFn={getAiExercises}
        setFooterActions={setActions}
        onSubmissionChange={setIsSubmitted}
        onExerciseDataChange={onExerciseDataChange}
      />
    </Container>
  );
}

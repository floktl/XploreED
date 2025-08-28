import { Container } from "../../../common/UI/UI";
import AIExerciseBlock from "../AIExercise/AIExerciseBlock";
import { getAiExercises } from "../../../../services/api";

export default function AIFeedbackContent({
	setActions,
	setIsSubmitted,
	onExerciseDataChange,
	setExerciseNavigation
}) {
	return (
		<Container>
			<AIExerciseBlock
				fetchExercisesFn={getAiExercises}
				setFooterActions={setActions}
				onSubmissionChange={setIsSubmitted}
				onExerciseDataChange={onExerciseDataChange}
				setExerciseNavigation={setExerciseNavigation}
			/>
		</Container>
	);
}

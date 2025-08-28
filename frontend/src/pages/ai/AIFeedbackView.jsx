import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import useAppStore from "../../store/useAppStore";
import { PageLayout } from "../../components/layout";
import {
	AIFeedbackContent,
	AIFeedbackFooter
} from "../../components/features/ai";

export default function AIFeedbackView() {
	const navigate = useNavigate();
	const darkMode = useAppStore((state) => state.darkMode);
	const username = useAppStore((state) => state.username);
	const isLoading = useAppStore((state) => state.isLoading);
	const isAdmin = useAppStore((state) => state.isAdmin);
	const [actions, setActions] = useState(null);
	const [isSubmitted, setIsSubmitted] = useState(false);
	const [exerciseTitle, setExerciseTitle] = useState(`${username}'s AI Exercises`);
	const [exerciseNavigation, setExerciseNavigation] = useState(null);

	useEffect(() => {
		if (!isLoading && (!username || isAdmin))
		{
			navigate(isAdmin ? "/admin-panel" : "/");
		}
	}, [username, isLoading, isAdmin, navigate]);

	const handleExerciseDataChange = (exerciseData) => {
		if (exerciseData && exerciseData.title)
		{
			setExerciseTitle(exerciseData.title);
		}
	};

	return (
		<PageLayout variant="flex">
			<AIFeedbackContent
				setActions={setActions}
				setIsSubmitted={setIsSubmitted}
				onExerciseDataChange={handleExerciseDataChange}
				setExerciseNavigation={setExerciseNavigation}
			/>
			<AIFeedbackFooter onNavigate={navigate} actions={actions} exerciseNavigation={exerciseNavigation} />
		</PageLayout>
	);
}

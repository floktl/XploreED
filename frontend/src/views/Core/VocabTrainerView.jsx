import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "../components/UI/UI";
import Alert from "../components/UI/Alert";
import useAppStore from "../store/useAppStore";
import { getNextVocabCard, submitVocabAnswer } from "../api";
import {
	VocabTrainerHeader,
	VocabCard,
	VocabTrainerFooter
} from "../components/VocabTrainer";

export default function VocabTrainerView() {
	const [card, setCard] = useState(null);
	const [show, setShow] = useState(false);
	const [loading, setLoading] = useState(true);

	const username = useAppStore((state) => state.username);
	const darkMode = useAppStore((state) => state.darkMode);
	const addBackgroundActivity = useAppStore((s) => s.addBackgroundActivity);
	const removeBackgroundActivity = useAppStore((s) => s.removeBackgroundActivity);
	const navigate = useNavigate();

	useEffect(() => {
		loadCard();
	}, []);

	const loadCard = async () => {
		setLoading(true);
		try {
			const data = await getNextVocabCard();
			setCard(data && data.id ? data : null);
			setShow(false);
		} catch {
			setCard(null);
		} finally {
			setLoading(false);
		}
	};

	const handleAnswer = async (quality) => {
		if (!card) return;

		// Add background activity for vocab update
		const vocabActivityId = `vocab-update-${Date.now()}`;
		addBackgroundActivity({
			id: vocabActivityId,
			label: "Updating vocabulary progress...",
			status: "In progress"
		});

		try {
			await submitVocabAnswer(card.id, quality);
			setTimeout(() => removeBackgroundActivity(vocabActivityId), 1200);
		} catch (error) {
			console.error("Failed to submit vocab answer:", error);
			setTimeout(() => removeBackgroundActivity(vocabActivityId), 1200);
		}

		loadCard();
	};

	return (
		<div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
			<Container>
				<VocabTrainerHeader />
				{loading ? (
					<Alert type="info">Loading...</Alert>
				) : !card ? (
					<Alert type="success">No cards due right now!</Alert>
				) : (
					<VocabCard
						card={card}
						show={show}
						onShowTranslation={() => setShow(true)}
						onAnswer={handleAnswer}
					/>
				)}
			</Container>
			<VocabTrainerFooter onNavigate={navigate} />
		</div>
	);
}

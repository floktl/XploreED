import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "../../components/common/UI/UI";
import Alert from "../../components/common/UI/Alert";
import useAppStore from "../../store/useAppStore";
import { getNextVocabCard, submitVocabAnswer } from "../../services/api";
import { PageLayout } from "../../components/layout";
import {
	VocabTrainerHeader,
	VocabCard,
	VocabTrainerFooter
} from "../../components/features/vocabulary";

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
		<PageLayout variant="relative">
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
		</PageLayout>
	);
}

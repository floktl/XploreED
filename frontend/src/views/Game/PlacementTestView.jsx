import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "../components/UI/UI";
import Footer from "../components/UI/Footer";
import useAppStore from "../store/useAppStore";
import {
	submitLevelAnswer,
	setUserLevel,
	generateAiFeedback,
} from "../api";
import PlacementFeedback from "../components/PlacementFeedback";
import {
	PlacementTestHeader,
	PlacementQuestion,
	PlacementControls
} from "../components/PlacementTest";

const SENTENCES = [
	"Ich bin Anna.",
	"Wir gehen heute einkaufen.",
	"Kannst du mir bitte helfen?",
	"Gestern habe ich einen interessanten Film gesehen.",
	"Obwohl es regnete, gingen wir spazieren.",
	"Wenn ich mehr Zeit hätte, würde ich ein Buch schreiben.",
	"Trotz seiner Müdigkeit arbeitete er bis spät in die Nacht.",
	"Hätte ich doch früher Deutsch gelernt!",
	"Der Politiker betonte, dass nachhaltige Energie entscheidend sei.",
	"Angesichts der aktuellen Lage wäre ein rasches Handeln der Regierung unerlässlich.",
];

function scramble(sentence) {
	return sentence.split(" ").sort(() => Math.random() - 0.5);
}

export default function PlacementTestView({ onComplete }) {
	const [index, setIndex] = useState(0);
	const [scrambled, setScrambled] = useState([]);
	const [sentence, setSentence] = useState("");
	const [answer, setAnswer] = useState("");
	const [correct, setCorrect] = useState(0);
	const [answers, setAnswers] = useState({});
	const [feedbackText, setFeedbackText] = useState("");
	const [feedbackSummary, setFeedbackSummary] = useState(null);
	const [showFeedback, setShowFeedback] = useState(false);
	const [finalScore, setFinalScore] = useState(0);
	const navigate = useNavigate();
	const darkMode = useAppStore((s) => s.darkMode);
	const setCurrentLevel = useAppStore((s) => s.setCurrentLevel);

	useEffect(() => {
		const s = SENTENCES[index];
		setSentence(s);
		setScrambled(scramble(s));
		setAnswer("");
	}, [index]);

	const handleNext = async () => {
		const trimmed = answer.trim();
		const locallyCorrect = trimmed === sentence;

		// fire-and-forget submission to keep UI responsive
		submitLevelAnswer(index, trimmed, sentence).catch((e) =>
			console.error("[PlacementTest] submit failed", e)
		);

		if (locallyCorrect) setCorrect((c) => c + 1);
		const id = `ex${index + 1}`;
		setAnswers((a) => ({ ...a, [id]: trimmed }));
		if (index < 9) {
			setIndex(index + 1);
		} else {
			const score = correct + (locallyCorrect ? 1 : 0);
			const finalAnswers = { ...answers, [id]: trimmed };
			const exerciseBlock = {
				exercises: SENTENCES.map((s, i) => ({
					id: `ex${i + 1}`,
					question: s,
				})),
			};

			try {
				const fb = await generateAiFeedback({ answers: finalAnswers, exercise_block: exerciseBlock });
				setFeedbackText(fb.feedbackPrompt || "");
				setFeedbackSummary(fb.summary || null);
			} catch (e) {
				console.error("[PlacementTest] AI feedback failed", e);
			}

			await setUserLevel(score);
			setCurrentLevel(score);
			setFinalScore(score);
			setShowFeedback(true);
		}
	};

	return (
		<>
			{showFeedback ? (
				<PlacementFeedback
					summary={feedbackSummary}
					onDone={() => {
						if (onComplete) {
							onComplete(finalScore);
						} else {
							navigate("/menu");
						}
					}}
				/>
			) : (
				<div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
					<Container>
						<PlacementTestHeader />
						<PlacementQuestion
							index={index}
							scrambled={scrambled}
							answer={answer}
							setAnswer={setAnswer}
						/>
						<PlacementControls onNext={handleNext} />
					</Container>
					<Footer />
				</div>
			)}
		</>
	);
}

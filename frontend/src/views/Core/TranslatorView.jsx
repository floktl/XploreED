import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "../components/UI/UI";
import useAppStore from "../store/useAppStore";
import { translateSentenceStream } from "../api";
import {
	TranslatorHeader,
	TranslationForm,
	TranslationFeedback,
	TranslatorFooter
} from "../components/Translator";

export default function TranslatorView() {
	const [english, setEnglish] = useState("");
	const [feedback, setFeedback] = useState("");
	const [studentInput, setStudentInput] = useState("");
	const [error, setError] = useState("");
	const [loading, setLoading] = useState(false);
	const [feedbackBlock, setFeedbackBlock] = useState(null);

	const username = useAppStore((state) => state.username);
	const setUsername = useAppStore((state) => state.setUsername);
	const darkMode = useAppStore((state) => state.darkMode);
	const isAdmin = useAppStore((state) => state.isAdmin);
	const addBackgroundActivity = useAppStore((s) => s.addBackgroundActivity);
	const removeBackgroundActivity = useAppStore((s) => s.removeBackgroundActivity);
	const navigate = useNavigate();

	useEffect(() => {
		if (isAdmin) {
			navigate("/admin-panel");
			return;
		}

		const storedUsername = localStorage.getItem("username");
		if (!username && storedUsername) {
			setUsername(storedUsername);
		}

		// Redirect if no session or stored username
		if (!username && !storedUsername) {
			navigate("/");
		}
	}, [isAdmin, username, setUsername, navigate]);

	const handleTranslate = async () => {
		setError("");
		setFeedbackBlock(null);

		if (!english.trim() || !studentInput.trim()) {
			setError("⚠️ Please fill out both fields before submitting.");
			return;
		}

		const payload = {
			english: String(english),
			student_input: String(studentInput),
		};

		// Add background activity for topic memory update
		const topicActivityId = `topic-${Date.now()}`;
		addBackgroundActivity({
			id: topicActivityId,
			label: "Updating topic memory...",
			status: "In progress"
		});

		try {
			setLoading(true);

			await translateSentenceStream(payload, (chunk) => {
				// Parse the JSON chunk to get feedbackBlock
				try {
					const data = JSON.parse(chunk);
					if (data.feedbackBlock) {
						setFeedbackBlock(data.feedbackBlock);
					}
				} catch (e) {
					console.error("[CLIENT] Failed to parse chunk:", chunk, e);
					// fallback: ignore
				}
			});

			setTimeout(() => removeBackgroundActivity(topicActivityId), 1200);
		} catch (err) {
			console.error("[CLIENT] Translation request failed:", err);
			setError("Something went wrong. Please try again.");
			setTimeout(() => removeBackgroundActivity(topicActivityId), 1200);
		} finally {
			setLoading(false);
		}
	};

	const handleReset = () => {
		setEnglish("");
		setStudentInput("");
		setFeedback("");
		setFeedbackBlock(null);
		setError("");
	};

	return (
		<div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
			<Container className="pb-20">
				<TranslatorHeader darkMode={darkMode} />

				<TranslationForm
					english={english}
					setEnglish={setEnglish}
					studentInput={studentInput}
					setStudentInput={setStudentInput}
					error={error}
					loading={loading}
					onTranslate={handleTranslate}
					darkMode={darkMode}
				/>

				<TranslationFeedback
					feedbackBlock={feedbackBlock}
					onReset={handleReset}
				/>
			</Container>

			<TranslatorFooter onNavigate={navigate} />
		</div>
	);
}

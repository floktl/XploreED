import React, { useState } from "react";
import { Container } from "../components/UI/UI";
import Footer from "../components/UI/Footer";
import useAppStore from "../store/useAppStore";
import { sendSupportFeedback } from "../api";
import {
	SupportHeader,
	SupportForm
} from "../components/Support";

export default function SupportView() {
	const darkMode = useAppStore((s) => s.darkMode);
	const [message, setMessage] = useState("");
	const [status, setStatus] = useState("");
	const [error, setError] = useState("");
	const [isSubmitting, setIsSubmitting] = useState(false);

	const handleSubmit = async (e) => {
		e.preventDefault();
		setError("");
		setStatus("");
		const trimmed = message.trim();
		if (!trimmed) {
			setError("Please enter a message.");
			return;
		}
		try {
			setIsSubmitting(true);
			const res = await sendSupportFeedback(trimmed);
			if (res && !res.error) {
				setStatus("Thanks! Your message was sent.");
				setMessage("");
			} else {
				setError(res?.error || "Failed to send feedback");
			}
		} catch (_) {
			setError("Failed to send feedback");
		} finally {
			setIsSubmitting(false);
		}
	};

	return (
		<div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
			<Container>
				<SupportHeader />
				<SupportForm
					message={message}
					setMessage={setMessage}
					error={error}
					status={status}
					isSubmitting={isSubmitting}
					onSubmit={handleSubmit}
					darkMode={darkMode}
				/>
			</Container>
			<Footer />
		</div>
	);
}

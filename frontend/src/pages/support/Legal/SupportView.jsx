import { useState } from "react";
import { Container } from "../../../components/common/UI/UI";
import Footer from "../../../components/common/UI/Footer";
import useAppStore from "../../../store/useAppStore";
import { sendSupportFeedback } from "../../../services/api";
import PageLayout from "../../../components/layout/PageLayout";
import {
  SupportHeader,
  SupportForm
} from "../../../components/features/support/Support";

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
		<PageLayout variant="relative">
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
		</PageLayout>
	);
}

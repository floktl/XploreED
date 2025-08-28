import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "../../components/common/UI/UI";
import useAppStore from "../../store/useAppStore";
import { getWeaknessLesson } from "../../services/api";
import { CheckCircle, Brain, BookOpen, Target, Sparkles } from "lucide-react";
import { PageLayout } from "../../components/layout";
import {
	AIWeaknessLessonHeader,
	AIWeaknessLessonProgress,
	AIWeaknessLessonContent,
	AIWeaknessLessonFooter
} from "../../components/features/ai";

export default function AIWeaknessLessonView() {
	const [html, setHtml] = useState("");
	const [error, setError] = useState("");
	const [loading, setLoading] = useState(true);
	const [progressPercentage, setProgressPercentage] = useState(0);
	const [progressStatus, setProgressStatus] = useState("Initializing...");
	const [progressIcon, setProgressIcon] = useState(Brain);
	const navigate = useNavigate();
	const username = useAppStore((state) => state.username);
	const setUsername = useAppStore((state) => state.setUsername);
	const darkMode = useAppStore((state) => state.darkMode);
	const isAdmin = useAppStore((state) => state.isAdmin);
	const isLoading = useAppStore((state) => state.isLoading);
	const addBackgroundActivity = useAppStore((s) => s.addBackgroundActivity);
	const removeBackgroundActivity = useAppStore((s) => s.removeBackgroundActivity);

	useEffect(() => {
		const stored = localStorage.getItem("username");
		if (!username && stored) {
			setUsername(stored);
		}
		if (!isLoading && (!username || isAdmin)) {
			navigate(isAdmin ? "/admin-panel" : "/");
		}
	}, [username, isAdmin, isLoading, navigate, setUsername]);

	useEffect(() => {
		let isMounted = true;
		let progressInterval;
		const progressSteps = [
			{ percentage: 15, status: "Analyzing your weaknesses...", icon: Target },
			{ percentage: 35, status: "Reviewing your past answers...", icon: BookOpen },
			{ percentage: 55, status: "Identifying weak topics...", icon: Brain },
			{ percentage: 75, status: "Generating personalized lesson...", icon: Sparkles },
			{ percentage: 90, status: "Finalizing your lesson...", icon: Sparkles },
			{ percentage: 99, status: "Ready!", icon: CheckCircle }
		];
		let currentStep = 0;
		progressInterval = setInterval(() => {
			if (currentStep < progressSteps.length) {
				const step = progressSteps[currentStep];
				setProgressPercentage(step.percentage);
				setProgressStatus(step.status);
				setProgressIcon(() => step.icon);
				currentStep++;
			} else {
				clearInterval(progressInterval);
			}
		}, 800);
		getWeaknessLesson()
			.then((data) => {
				if (isMounted) {
					setHtml(data);
					setLoading(false);
					setProgressPercentage(99);
					setProgressStatus("Ready!");
					setProgressIcon(() => CheckCircle);

					// Add background activity for topic memory update
					const topicActivityId = `weakness-topic-${Date.now()}`;
					addBackgroundActivity({
						id: topicActivityId,
						label: "Updating topic memory from lesson...",
						status: "In progress"
					});

					// Remove background activity after a delay
					setTimeout(() => removeBackgroundActivity(topicActivityId), 1200);
				}
			})
			.catch((err) => {
				console.error("Failed to load lesson", err);
				setError("🚨 500: Mistral API Error. Please try again later.");
				setLoading(false);
				const topicActivityId = `weakness-topic-${Date.now()}`;
				addBackgroundActivity({
					id: topicActivityId,
					label: "Updating topic memory from lesson...",
					status: "In progress"
				});
				setTimeout(() => removeBackgroundActivity(topicActivityId), 1200);
			})
			.finally(() => {
				clearInterval(progressInterval);
			});
		return () => {
			isMounted = false;
			clearInterval(progressInterval);
		};
	}, []);

	return (
		<PageLayout variant="relative">
			<Container>
				<AIWeaknessLessonHeader />
				{loading ? (
					<AIWeaknessLessonProgress
						progressPercentage={progressPercentage}
						progressStatus={progressStatus}
						progressIcon={progressIcon}
					/>
				) : (
					<AIWeaknessLessonContent html={html} error={error} />
				)}
			</Container>
			<AIWeaknessLessonFooter onNavigate={navigate} />
		</PageLayout>
	);
}

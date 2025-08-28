import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Alert from "../../components/common/UI/Alert";
import { Container } from "../../components/common/UI/UI";
import useAppStore from "../../store/useAppStore";
import { getStudentLessons } from "../../services/api";
import { PageLayout } from "../../components/layout";
import {
	LessonsHeader,
	LessonsList,
	LessonsLoading,
	LessonsFooter
} from "../../components/features/lessons";

export default function LessonsView() {
	const [lessons, setLessons] = useState([]);
	const [error, setError] = useState("");
	const [isLoadingLessons, setIsLoadingLessons] = useState(true);
	const navigate = useNavigate();
	const darkMode = useAppStore((state) => state.darkMode);
	const username = useAppStore((state) => state.username);
	const isLoading = useAppStore((state) => state.isLoading);
	const isAdmin = useAppStore((state) => state.isAdmin);
	const setCurrentPageContent = useAppStore((s) => s.setCurrentPageContent);
	const clearCurrentPageContent = useAppStore((s) => s.clearCurrentPageContent);

	useEffect(() => {
		if (!isLoading && (!username || isAdmin)) {
			navigate(isAdmin ? "/admin-panel" : "/");
		}
	}, [username, isLoading, isAdmin, navigate]);

	useEffect(() => {
		if (!username) return;

		const fetchLessons = async () => {
			try {
				setIsLoadingLessons(true);
				setError("");
				const data = await getStudentLessons(); // ✅ use central API helper
				// Handle the API response structure - data.lessons contains the array
				const lessonsArray = data.lessons || [];
				setLessons(lessonsArray);
			} catch (err) {
				console.error("[CLIENT] Failed to load lessons:", err);
				setError("Could not load lessons. Please try again later.");
				setLessons([]); // Set empty array on error
			} finally {
				setIsLoadingLessons(false);
			}
		};

		fetchLessons();
	}, [username]);

	useEffect(() => {
		setCurrentPageContent({
			type: "lessons",
			username,
			lessons
		});
		return () => clearCurrentPageContent();
	}, [username, lessons, setCurrentPageContent, clearCurrentPageContent]);

	return (
		<PageLayout variant="relative">
			<Container>
				<LessonsHeader darkMode={darkMode} />
				{error && <Alert type="danger">{error}</Alert>}
				{isLoadingLessons && !error ? (
					<LessonsLoading />
				) : (
					lessons.length === 0 && !error ? (
						<Alert type="info">No lessons yet. Start practicing to track your progress!</Alert>
					) : (
						<LessonsList lessons={lessons} />
					)
				)}
			</Container>
			<LessonsFooter />
		</PageLayout>
	);
}

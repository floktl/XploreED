import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";
import { ArrowLeft } from "lucide-react";
import useAppStore from "../store/useAppStore";
import { getStudentLessons } from "../api";


export default function Lessons() {
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
		<div className={`relative min-h-screen ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
			<Container>
				<p className={`text-center ${darkMode ? "text-gray-300" : "text-gray-600"}`}>
					Overview of your past and upcoming lessons
				</p>

				{error && <Alert type="danger">{error}</Alert>}

				{isLoadingLessons && !error ? (
					<div className="flex items-center justify-center py-8">
						<div className="flex items-center space-x-3">
							<div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
							<span className="text-gray-600 dark:text-gray-300">Loading lessons...</span>
						</div>
					</div>
				) : (
					lessons.length === 0 && !error ? (
						<Alert type="info">No lessons yet. Start practicing to track your progress!</Alert>
					) : (
						<div className="flex flex-col gap-4">
							{(() => {
								// Ensure lessons is an array before filtering
								const lessonsArray = Array.isArray(lessons) ? lessons : [];

								const completed = lessonsArray
									.filter((l) => l.completed)
									.sort((a, b) => a.lesson_id - b.lesson_id);

								const nextUnfinished = lessonsArray
									.filter((l) => !l.completed)
									.sort((a, b) => a.lesson_id - b.lesson_id)[0];

								const visibleLessons = nextUnfinished
									? [...completed, nextUnfinished]
									: completed;

								return visibleLessons.map((lesson) => (

									<Card key={lesson.lesson_id}>
										<div className="flex justify-between items-center">
											<div className="flex justify-start items-baseline w-1/2 min-w-0 overflow-hidden">
												<h3 className="font-semibold truncate" title={lesson.title}>{lesson.title || `Lesson ${lesson.lesson_id}`}</h3>
												<p className={`text-sm mx-2 flex items-center space-x-1 ${lesson.completed ? "text-green-600" : "text-gray-500"}`}>
													{lesson.completed ? (
														<>
															<span className="text-base">✅</span>
															<span>Completed</span>
														</>
													) : (
														<>
															<span className="text-base">📊</span>
															<span>{Math.round(lesson.percent_complete || 0)}% Complete</span>
														</>
													)}
												</p>
												{lesson.last_attempt && (
													<p className="text-xs text-gray-400">
														Last Attempt: {new Date(lesson.last_attempt).toLocaleString()}
													</p>
												)}
											</div>
											<Button
												variant="secondary"
												type="button"
												className="relative overflow-hidden w-1/2"
												onClick={() => navigate(`/lesson/${lesson.lesson_id}`)}
											>
												<span className="relative z-10">
													{lesson.completed ? "🔁 Review" : "▶️ Continue"}
												</span>
												{!lesson.completed && (
													<span
														className="absolute top-0 left-0 h-full bg-blue-500 opacity-30"
														style={{ width: `${lesson.percent_complete || 0}%` }}
													/>
												)}
											</Button>
										</div>
									</Card>
								));
							})()}
						</div>
					)
				)}

			</Container>
			<Footer>
				<Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")} className="gap-2">
					<ArrowLeft />
					Back
				</Button>
			</Footer>
		</div>
	);
}

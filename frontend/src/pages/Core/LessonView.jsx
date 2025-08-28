import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import useAppStore from "../../store/useAppStore";
import { Container } from "../../components/common/UI/UI";
import { PageLayout } from "../../components/layout";
import {
	getLesson,
	getLessonProgress,
	isLessonCompleted,
	markLessonComplete,
	updateLessonBlockProgress,
} from "../../services/api";
import {
	  LessonsHeader,
} from "../../components/features/lessons";
import LessonProgress from "../../components/Lesson/LessonProgress";
import LessonContent from "../../components/Lesson/LessonContent";
import LessonFooter from "../../components/Lesson/LessonFooter";

export default function LessonView() {
	const { lessonId } = useParams();
	const [entries, setEntries] = useState([]);
	const [progress, setProgress] = useState({});
	const [percentComplete, setPercentComplete] = useState(0);
	const [canComplete, setCanComplete] = useState(false);
	const [markedComplete, setMarkedComplete] = useState(false);
	const [showAi, setShowAi] = useState(false);
	const [fatalError, setFatalError] = useState(false);
	const navigate = useNavigate();
	const isAdmin = useAppStore((state) => state.isAdmin);
	const [numBlocks, setNumBlocks] = useState(0);
	const [actions, setActions] = useState(null);
	const setCurrentPageContent = useAppStore((s) => s.setCurrentPageContent);
	const clearCurrentPageContent = useAppStore((s) => s.clearCurrentPageContent);

	useEffect(() => {
		if (isAdmin) {
			navigate("/admin-panel");
			return;
		}

		const fetchLesson = async () => {
			try {
				const data = await getLesson(lessonId);
				if (data && !Array.isArray(data)) {
					setEntries([data]);
					setNumBlocks(data.num_blocks || 0);
				}
			} catch (err) {
				console.error("🔥 Exception while loading lesson content:", err);
				setFatalError(true);
			}
		};

		const fetchProgress = async () => {
			try {
				const data = await getLessonProgress(lessonId);
				console.log("🔍 Initial progress data:", data);
				setProgress(data);
			} catch (err) {
				console.warn("Could not load progress", err);
				setFatalError(true);
			}
		};

		fetchLesson();
		fetchProgress();
		// Removed fetchMarkedComplete since completion status is now calculated from progress
	}, [lessonId, isAdmin, navigate]);

	useEffect(() => {
		setCurrentPageContent({
			type: "lesson-view",
			lessonId,
			entries,
			progress,
			percentComplete,
			canComplete
		});
		return () => clearCurrentPageContent();
	}, [lessonId, entries, progress, percentComplete, canComplete, setCurrentPageContent, clearCurrentPageContent]);

	useEffect(() => {
		const completed = Object.values(progress).filter(Boolean).length;
		console.log("🔍 Progress debug:", { progress, completed, numBlocks });
		setPercentComplete(numBlocks > 0 ? (completed / numBlocks) * 100 : 0);
		setCanComplete(numBlocks === 0 || completed === numBlocks);

		// Calculate completion status based on actual progress, not API response
		const actualCompleted = completed >= numBlocks;
		setMarkedComplete(actualCompleted);

		console.log("🔍 Can complete:", numBlocks === 0 || completed === numBlocks);
		console.log("🔍 Actual completed:", actualCompleted);
	}, [progress, numBlocks]);

	const handleMarkComplete = async () => {
		if (!canComplete) {
			alert("⚠️ Please complete all blocks before marking the lesson as done.");
			return;
		}

		try {
			await markLessonComplete(lessonId);
			setMarkedComplete(true);
			navigate("/lessons");
		} catch (err) {
			console.error("❌ Could not mark lesson complete:", err);
			alert("Failed to mark lesson complete.");
			setFatalError(true);
		}
	};

	// Refresh progress after each toggle to ensure state synchronization
	const refreshProgress = async () => {
		try {
			const data = await getLessonProgress(lessonId);
			console.log("🔍 Refreshed progress data:", data);
			setProgress(data);
		} catch (err) {
			console.warn("Could not refresh progress", err);
		}
	};

	// Refresh completion status after each toggle
	const refreshCompletionStatus = async () => {
		try {
			// Calculate completion status based on actual progress
			const completed = Object.values(progress).filter(Boolean).length;
			const actualCompleted = completed >= numBlocks;
			console.log("🔍 Refreshed completion status based on progress:", { completed, numBlocks, actualCompleted });
			setMarkedComplete(actualCompleted);
		} catch (err) {
			console.warn("Could not refresh completion status", err);
		}
	};

	if (fatalError) {
		return <ErrorPageView />;
	}

	return (
		<PageLayout variant="relative">
			<Container>
				        <LessonsHeader />

				{entries.length > 0 && (
					<LessonProgress
						percentComplete={percentComplete}
						markedComplete={markedComplete}
						canComplete={canComplete}
						onMarkComplete={handleMarkComplete}
					/>
				)}

				<LessonContent
					entries={entries}
					progress={progress}
					setActions={setActions}
					lessonId={lessonId}
					showAi={showAi}
					setShowAi={setShowAi}
					updateLessonBlockProgress={updateLessonBlockProgress}
					refreshProgress={refreshProgress}
					refreshCompletionStatus={refreshCompletionStatus}
					setFatalError={setFatalError}
					markedComplete={markedComplete}
				/>
			</Container>

			<LessonFooter
				actions={actions}
				onNavigate={navigate}
			/>
		</PageLayout>
	);
}

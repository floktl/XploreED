import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import useAppStore from "../store/useAppStore";
import BlockContentRenderer from "./BlockContentRenderer";
import AIExerciseBlock from "./AIExerciseBlock";
import Card from "./UI/Card";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";
import { ArrowLeft } from "lucide-react";
import Footer from "./UI/Footer";
import ErrorPage from "./ErrorPage";
import {
    getLesson,
    getLessonProgress,
    isLessonCompleted,
    markLessonComplete,
    updateLessonBlockProgress,
} from "../api";

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
        return <ErrorPage />;
    }

    return (
        <div className="relative min-h-screen pb-20 bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white">
            <Container className="pb-20">
                <Title className="mb-4 text-3xl font-bold">Lesson</Title>

                {entries.length > 0 && (
                    <div className="mb-6">
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            Progress: {Math.round(percentComplete)}%
                        </p>
                        <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded">
                            <div
                                className="h-2 bg-green-500 rounded"
                                style={{ width: `${percentComplete}%` }}
                            ></div>
                        </div>

                        <div className="mt-4 text-right">
                            <Button
                                variant={markedComplete ? "secondary" : "success"}
                                disabled={!canComplete || markedComplete}
                                onClick={handleMarkComplete}
                            >
                                {markedComplete ? "✅ Marked as Completed" : "✅ Mark Lesson as Completed"}
                            </Button>
                        </div>
                    </div>
                )}

                {entries.length === 0 ? (
                    <p>No content found.</p>
                ) : (
                    <div className="space-y-4">
                        {entries.map((entry, i) => (
                            <Card key={i}>
                                <h3 className="text-xl font-semibold">{entry.title}</h3>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    Added on {new Date(entry.created_at).toLocaleString()}
                                </p>
                                <BlockContentRenderer
                                    html={entry.content}
                                    progress={progress}
                                    mode="student"
                                    setFooterActions={setActions}
                                    onToggle={async (blockId, completed) => {
                                        console.log("🔍 Toggle debug:", { blockId, completed, lessonId });
                                        console.log("🔍 Current progress before toggle:", progress);
                                        console.log("🔍 Current markedComplete:", markedComplete);
                                        try {
                                            await updateLessonBlockProgress(lessonId, blockId, completed);
                                            console.log("🔍 API call successful, refreshing progress...");
                                            await refreshProgress(); // Refresh progress after each toggle
                                            await refreshCompletionStatus(); // Refresh completion status after each toggle
                                            console.log("🔍 Progress and completion status refreshed");
                                        } catch (err) {
                                            console.error("❌ Failed to update progress", err);
                                            setFatalError(true);
                                        }
                                    }}
                                />
                                {entry.ai_enabled && (
                                    <div className="mt-4">
                                        {showAi ? (
                                            <AIExerciseBlock
                                                blockId={`lesson-${lessonId}-ai`}
                                                setFooterActions={setActions}
                                            />
                                        ) : (
                                            <Button variant="secondary" onClick={() => setShowAi(true)}>
                                                Start AI Exercises
                                            </Button>
                                        )}
                                    </div>
                                )}
                            </Card>
                        ))}
                    </div>
                )}

            </Container>
            <Footer>
                <div className="flex gap-2">
                    {actions}
                    <Button
                        size="sm"
                        variant="ghost"
                        type="button"
                        onClick={() => navigate("/lessons")}
                        className="gap-2 rounded-full"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to Lessons
                    </Button>
                </div>
            </Footer>
        </div>
    );
}

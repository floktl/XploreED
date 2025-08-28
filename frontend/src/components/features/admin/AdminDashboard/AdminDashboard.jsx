import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container, Title } from "../../../common/UI/UI";
import Button from "../../../common/UI/Button";
import Alert from "../../../common/UI/Alert";
import Footer from "../../../common/UI/Footer";
import Modal from "../../../common/UI/Modal";
import ErrorPageView from "../../../../pages/Core/ErrorPageView";
import useAppStore from "../../../../store/useAppStore";
import { useRequireAdmin } from "../../../../hooks";
import { LessonEditor } from "../../lessons";
import { BlockContentRenderer } from "../../../common";
import {
    getAdminRole,
    getAdminResults,
    getLessons,
    getLessonProgressSummary,
    getLessonProgressDetails,
    saveLesson,
    togglePublishLesson,
    deleteLesson,
    fetchSupportFeedback,
    getAiLesson
} from "../../../../services/api";

// Import modular components
import UserManagement from "./Management/UserManagement";
import LessonManagement from "./Management/LessonManagement";
import FeedbackManagement from "./Management/FeedbackManagement";

export default function AdminDashboard() {
    useRequireAdmin();
    const [results, setResults] = useState([]);
    const [error, setError] = useState("");
    const [modalContent, setModalContent] = useState(null);
    const [showEditorModal, setShowEditorModal] = useState(false);
    const [newLessonId, setNewLessonId] = useState("");
    const [newContent, setNewContent] = useState("");
    const [newTitle, setNewTitle] = useState("");
    const [aiEnabled, setAiEnabled] = useState(false);
    const [lessons, setLessons] = useState([]);
    const [lessonProgress, setLessonProgress] = useState({});
    const [showLessonModal, setShowLessonModal] = useState(null);
    const [lessonProgressDetails, setLessonProgressDetails] = useState([]);
    const [supportFeedback, setSupportFeedback] = useState([]);
    const [formError, setFormError] = useState("");
    const [isEditing, setIsEditing] = useState(false);
    const [fatalError, setFatalError] = useState(false);
    const [deleteModal, setDeleteModal] = useState({ show: false, lesson: null });
    const setIsAdmin = useAppStore((state) => state.setIsAdmin);

    const navigate = useNavigate();
    const darkMode = useAppStore((state) => state.darkMode);
    const isAdmin = useAppStore((state) => state.isAdmin);
    const isLoading = useAppStore((state) => state.isLoading);

    // Helper to normalize API response shape for feedback list
    const toFeedbackArray = (data) => (Array.isArray(data) ? data : Array.isArray(data?.feedback) ? data.feedback : []);

    // Handle lesson deletion confirmation
    const handleDeleteLesson = async (lesson) => {
        try {
            const deleted = await deleteLesson(lesson.lesson_id);
            if (deleted.ok || deleted === true) {
                setLessons((prev) => prev.filter((l) => l.lesson_id !== lesson.lesson_id));
                setDeleteModal({ show: false, lesson: null });
            }
        } catch (err) {
            console.error("❌ Failed to delete lesson", err);
            setFatalError(true);
        }
    };

    // Handle feedback deletion
    const handleDeleteFeedback = async (feedbackId) => {
        try {
            // Implementation would go here - this is a simplified version
            setSupportFeedback(prev => prev.filter(fb => fb.id !== feedbackId));
        } catch (err) {
            console.error("❌ Failed to delete feedback", err);
            setFatalError(true);
        }
    };

    // Handle lesson editing
    const handleEditLesson = (lesson) => {
        setIsEditing(true);
        setNewLessonId(lesson.lesson_id);
        setNewTitle(lesson.title);
        setNewContent(lesson.content || "");
        setFormError("");
        setAiEnabled(false);
        setShowEditorModal(true);
    };

    useEffect(() => {
        const verifyAdmin = async () => {
            try {
                const data = await getAdminRole();
                setIsAdmin(data.is_admin);

                if (!data.is_admin) {
                    navigate("/admin-login");
                    return;
                }

                // Load admin data
                const [resultsData, lessonsData, feedbackData] = await Promise.all([
                    getAdminResults(),
                    getLessons(),
                    fetchSupportFeedback()
                ]);

                setResults(resultsData || []);
                setLessons(Array.isArray(lessonsData) ? lessonsData : []);
                setSupportFeedback(toFeedbackArray(feedbackData));

                // Load lesson progress summary
                try {
                    const progressData = await getLessonProgressSummary();
                    setLessonProgress(progressData || {});
                } catch (err) {
                    console.warn("Failed to load lesson progress:", err);
                }
            } catch (err) {
                console.error("❌ Admin verification failed", err);
                setError("Failed to verify admin status");
            }
        };

        verifyAdmin();
    }, [navigate, setIsAdmin]);

    if (fatalError) {
        return <ErrorPageView />;
    }

    if (isLoading) {
        return (
            <Container>
                <div className="flex justify-center items-center min-h-screen">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                        <p>Loading admin dashboard...</p>
                    </div>
                </div>
            </Container>
        );
    }

    return (
        <Container>
            <div className="min-h-screen py-8">
                <div className="mb-8">
                    <Title>Admin Dashboard</Title>
                    {error && (
                        <Alert variant="error" className="mt-4">
                            {error}
                        </Alert>
                    )}
                </div>

                {/* User Management Section */}
                <UserManagement
                    results={results}
                    darkMode={darkMode}
                />

                {/* Lesson Management Section */}
                <LessonManagement
                    lessons={lessons}
                    lessonProgress={lessonProgress}
                    darkMode={darkMode}
                    setIsEditing={setIsEditing}
                    setNewLessonId={setNewLessonId}
                    setNewTitle={setNewTitle}
                    setNewContent={setNewContent}
                    setFormError={setFormError}
                    setAiEnabled={setAiEnabled}
                    setShowEditorModal={setShowEditorModal}
                    getLessonProgressDetails={getLessonProgressDetails}
                    setLessonProgressDetails={setLessonProgressDetails}
                    setShowLessonModal={setShowLessonModal}
                    setFatalError={setFatalError}
                    setModalContent={setModalContent}
                    handleEditLesson={handleEditLesson}
                    togglePublishLesson={togglePublishLesson}
                    getLessons={getLessons}
                    setLessons={setLessons}
                    setDeleteModal={setDeleteModal}
                />

                {/* Feedback Management Section */}
                <FeedbackManagement
                    supportFeedback={supportFeedback}
                    darkMode={darkMode}
                    handleDeleteFeedback={handleDeleteFeedback}
                />

                {/* Modals */}
                {showEditorModal && (
                    <Modal onClose={() => setShowEditorModal(false)}>
                        <LessonEditor
                            lessonId={newLessonId}
                            title={newTitle}
                            content={newContent}
                            aiEnabled={aiEnabled}
                            isEditing={isEditing}
                            onSave={async (lessonData) => {
                                try {
                                    await saveLesson(lessonData);
                                    const refreshed = await getLessons();
                                    setLessons(Array.isArray(refreshed) ? refreshed : []);
                                    setShowEditorModal(false);
                                } catch (err) {
                                    console.error("❌ Failed to save lesson", err);
                                    setFormError("Failed to save lesson");
                                }
                            }}
                            onCancel={() => setShowEditorModal(false)}
                            error={formError}
                        />
                    </Modal>
                )}

                {modalContent && (
                    <Modal onClose={() => setModalContent(null)}>
                        <div className="max-w-4xl max-h-[80vh] overflow-y-auto">
                            <h2 className="text-xl font-bold mb-4">{modalContent.title}</h2>
                            <BlockContentRenderer content={modalContent.content} />
                        </div>
                    </Modal>
                )}

                {showLessonModal && (
                    <Modal onClose={() => setShowLessonModal(null)}>
                        <div className="max-w-4xl max-h-[80vh] overflow-y-auto">
                            <h2 className="text-xl font-bold mb-4">Lesson Progress Details</h2>
                            <div className="space-y-4">
                                {lessonProgressDetails.map((detail, index) => (
                                    <div key={index} className="p-4 border rounded-lg">
                                        <h3 className="font-semibold mb-2">{detail.username}</h3>
                                        <p>Progress: {detail.progress}%</p>
                                        <p>Last Activity: {new Date(detail.last_activity).toLocaleString()}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </Modal>
                )}

                {deleteModal.show && (
                    <Modal onClose={() => setDeleteModal({ show: false, lesson: null })}>
                        <div className="text-center">
                            <h3 className="text-lg font-semibold mb-4">Confirm Deletion</h3>
                            <p className="mb-6">
                                Are you sure you want to delete lesson "{deleteModal.lesson?.title}"?
                                This action cannot be undone.
                            </p>
                            <div className="flex gap-4 justify-center">
                                <Button
                                    variant="danger"
                                    onClick={() => handleDeleteLesson(deleteModal.lesson)}
                                >
                                    Delete
                                </Button>
                                <Button
                                    variant="secondary"
                                    onClick={() => setDeleteModal({ show: false, lesson: null })}
                                >
                                    Cancel
                                </Button>
                            </div>
                        </div>
                    </Modal>
                )}
            </div>
            <Footer />
        </Container>
    );
}

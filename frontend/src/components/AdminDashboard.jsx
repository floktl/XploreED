import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";
import { Input } from "./UI/UI";
import {
    Search,
    Pencil,
    Ban,
    Megaphone,
    X,
    Save,
    Rocket,
    Users,
    BookOpen,
    MessageSquare,
    BarChart3,
    Plus,
    Eye,
    Trash2,
    Settings,
    Calendar,
    User,
    Target,
    ArrowRight,
    Shield
} from "lucide-react";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import ErrorPage from "./ErrorPage";
import Footer from "./UI/Footer";
import Modal from "./UI/Modal";
import useAppStore from "../store/useAppStore";
import useRequireAdmin from "../hooks/useRequireAdmin";
import LessonEditor from "./LessonEditor";
import BlockContentRenderer from "./BlockContentRenderer";
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
} from "../api";

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

    useEffect(() => {
        const verifyAdmin = async () => {
            try {
                const data = await getAdminRole();
                setIsAdmin(data.is_admin);

                if (!data.is_admin) {
                    navigate("/admin-login");
                    return;
                }

                // Load data but don't crash dashboard if one fails
                const [resResults, resLessons, resProgress, resFeedback] = await Promise.allSettled([
                    getAdminResults(),
                    getLessons(),
                    getLessonProgressSummary(),
                    fetchSupportFeedback(),
                ]);

                if (resResults.status === "fulfilled") setResults(resResults.value);
                if (resLessons.status === "fulfilled") setLessons(Array.isArray(resLessons.value) ? resLessons.value : []);
                if (resProgress.status === "fulfilled") setLessonProgress(resProgress.value);
                if (resFeedback.status === "fulfilled") setSupportFeedback(toFeedbackArray(resFeedback.value));

                if (
                    resResults.status === "rejected" ||
                    resLessons.status === "rejected" ||
                    resProgress.status === "rejected" ||
                    resFeedback.status === "rejected"
                ) {
                    console.warn("Some admin data failed to load:", {
                        results: resResults.status,
                        lessons: resLessons.status,
                        progress: resProgress.status,
                        feedback: resFeedback.status,
                    });
                }

            } catch (err) {
                console.error("❌ Admin verification failed:", err);
                // Only show fatal error if role check itself fails
                setFatalError(true);
            }
        };

        verifyAdmin();
    }, [navigate, setIsAdmin]);

    // Live refresh: poll feedback every 5 seconds so new messages appear automatically
    useEffect(() => {
        let intervalId;
        const poll = async () => {
            try {
                const data = await fetchSupportFeedback();
                setSupportFeedback(toFeedbackArray(data));
            } catch (e) {
                // ignore transient errors; keep polling
            }
        };
        // start immediately and then poll
        poll();
        intervalId = setInterval(poll, 5000);
        return () => clearInterval(intervalId);
    }, []);

    // Handle fatal render after all hooks have been declared to avoid hook order changes
    if (fatalError) {
        return <ErrorPage />;
    }

    const userSummary = results.reduce((acc, curr) => {
        const { username, timestamp, level } = curr;
        if (!acc[username] || new Date(timestamp) > new Date(acc[username].lastTime || 0)) {
            acc[username] = { username, lastLevel: level, lastTime: timestamp };
        }
        return acc;
    }, {});

    const handleEditLesson = (lesson) => {
        setNewLessonId(lesson.lesson_id);
        setNewTitle(lesson.title);
        setNewContent(lesson.content);
        setAiEnabled(!!lesson.ai_enabled);
        setIsEditing(true);
        setShowEditorModal(true);
        setFormError("");
    };

    const handleSaveLesson = async (publish = false) => {
        setFormError("");

        if (!newTitle || !newContent || !newLessonId) {
            setFormError("Please fill out all fields.");
            return;
        }

        const duplicateId = lessons.find(
            (l) => l.lesson_id === parseInt(newLessonId)
        );
        const duplicateTitle = lessons.find(
            (l) =>
                l.title.trim().toLowerCase() === newTitle.trim().toLowerCase() &&
                (!isEditing || l.lesson_id !== parseInt(newLessonId))
        );

        if (!isEditing && duplicateId) {
            setFormError(`Lesson ID ${newLessonId} already exists. Please choose a different ID.`);
            return;
        }

        if (duplicateTitle) {
            setFormError(`Lesson title "${newTitle}" already exists. Please choose a different title.`);
            return;
        }

        try {
            const lessonPayload = {
                lesson_id: parseInt(newLessonId),
                title: newTitle,
                content: newContent,
                published: publish ? 1 : 0,
                ai_enabled: aiEnabled ? 1 : 0,
            };

            const res = await saveLesson(lessonPayload, isEditing);

            if (!res.ok) {
                setFormError("Failed to save lesson.");
                return;
            }

            const updatedLessons = await getLessons();
            setLessons(Array.isArray(updatedLessons) ? updatedLessons : []);

            // Clear UI state
            setShowEditorModal(false);
            setNewLessonId("");
            setNewTitle("");
            setNewContent("");
            setFormError("");
            setIsEditing(false);
            setAiEnabled(false);
        } catch (err) {
            console.error("Error saving lesson:", err);
            setFormError("Could not save lesson.");
            setFatalError(true);
        }
    };

    const handleDeleteFeedback = async (id) => {
        try {
            const { deleteSupportFeedback } = await import("../api");
            await deleteSupportFeedback(id);
            setSupportFeedback((list) => list.filter((f) => f.id !== id));
        } catch (e) {
            console.error("Failed to delete feedback", e);
        }
    };

    return (
        <Container>
                                            <div className={`relative min-h-screen pb-20 overflow-hidden ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
                    <div className="h-full overflow-y-auto px-4">
                        <div className="flex items-center justify-between mb-6">
                            <Link
                                to="/admin-users"
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition-colors ${
                                    darkMode
                                        ? "bg-gray-700 hover:bg-gray-600 text-white"
                                        : "bg-blue-50 hover:bg-blue-100 text-blue-700"
                                }`}
                            >
                                <Users className="w-4 h-4" />
                                Manage Users
                                <ArrowRight className="w-4 h-4" />
                            </Link>
                        </div>

                        {error && <Alert type="danger">{error}</Alert>}

                {/* User Activity Section */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <Users className={`w-6 h-6 ${darkMode ? "text-blue-400" : "text-blue-600"}`} />
                        <h2 className="text-xl font-bold">User Activity</h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className={`min-w-full border rounded-lg ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
                            <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
                                <tr>
                                    <th className="px-4 py-3 text-left font-semibold">User</th>
                                    <th className="px-4 py-3 text-left font-semibold">Level</th>
                                    <th className="px-4 py-3 text-left font-semibold">Last Activity</th>
                                    <th className="px-4 py-3 text-left font-semibold">Actions</th>
                                </tr>
                            </thead>
                            <tbody className={darkMode ? "bg-gray-800 divide-gray-700" : "bg-white divide-gray-200"}>
                                {Object.values(userSummary).length === 0 ? (
                                    <tr>
                                        <td colSpan={4} className="px-4 py-8 text-center text-gray-400 italic">
                                            <User className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                            No users found
                                        </td>
                                    </tr>
                                ) : (
                                    Object.values(userSummary).map((u) => (
                                        <tr key={u.username} className={`${darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"} transition-colors`}>
                                            <td className="px-4 py-3 font-semibold">{u.username}</td>
                                            <td className="px-4 py-3">
                                                <div className="flex items-center gap-2">
                                                    <Target className="w-4 h-4 text-green-500" />
                                                    {u.lastLevel ?? "—"}
                                                </div>
                                            </td>
                                            <td className="px-4 py-3">
                                                <div className="flex items-center gap-2">
                                                    <Calendar className="w-4 h-4 text-gray-400" />
                                                    {u.lastTime ? new Date(u.lastTime).toLocaleString() : "—"}
                                                </div>
                                            </td>
                                            <td className="px-4 py-3">
                                                <Link
                                                    to="/profile-stats"
                                                    state={{ username: u.username }}
                                                    className={`inline-flex items-center gap-2 px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                                                        darkMode
                                                            ? "text-blue-400 hover:text-blue-300 hover:bg-gray-700"
                                                            : "text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                                    }`}
                                                >
                                                    <BarChart3 className="w-4 h-4" />
                                                    View Stats
                                                </Link>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Lessons Management Section */}
                <div className="mb-8">
                    <div className="flex justify-between items-center mb-6">
                        <div className="flex items-center gap-3">
                            <BookOpen className={`w-6 h-6 ${darkMode ? "text-blue-400" : "text-blue-600"}`} />
                            <h2 className="text-xl font-bold">Lesson Management</h2>
                        </div>
                        <Button
                            variant="success"
                            size="auto"
                            onClick={() => {
                                setIsEditing(false);
                                setNewLessonId("");
                                setNewTitle("");
                                setNewContent("");
                                setFormError("");
                                setAiEnabled(false);
                                setShowEditorModal(true);
                            }}
                            className="gap-2"
                        >
                            <Plus className="w-4 h-4" />
                            Add Lesson
                        </Button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className={`min-w-full border rounded-lg overflow-hidden ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
                            <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
                                <tr>
                                    <th className="px-4 py-3 text-left font-semibold">ID</th>
                                    <th className="px-4 py-3 text-left font-semibold">Title</th>
                                    <th className="px-4 py-3 text-left font-semibold">Progress</th>
                                    <th className="px-4 py-3 text-left font-semibold">Target</th>
                                    <th className="px-4 py-3 text-left font-semibold">Actions</th>
                                </tr>
                            </thead>
                            <tbody className={darkMode ? "bg-gray-800 divide-gray-700" : "bg-white divide-gray-200"}>
                                {lessons.map((lesson) => {
                                    const isDraft = lesson.published === 0;

                                    return (
                                        <tr key={lesson.lesson_id} className={`${darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"} transition-colors`}>
                                            <td className={`px-4 py-3 ${isDraft ? "text-gray-400 italic" : ""}`}>
                                                {lesson.lesson_id}
                                            </td>
                                            <td className={`px-4 py-3 ${isDraft ? "text-gray-400 italic" : ""}`}>
                                                {lesson.title}
                                            </td>
                                            <td className="px-4 py-3">
                                                {lesson.published ? (
                                                    lesson.num_blocks === 0 ? (
                                                        <Button
                                                            variant="ghost"
                                                            disabled
                                                            className="opacity-60 cursor-not-allowed"
                                                        >
                                                            <Settings className="w-4 h-4" />
                                                        </Button>
                                                    ) : (
                                                        <Button
                                                            variant="progress"
                                                            size="auto"
                                                            onClick={async () => {
                                                                try {
                                                                    const data = await getLessonProgressDetails(lesson.lesson_id);
                                                                    setLessonProgressDetails(data);
                                                                    setShowLessonModal(lesson.lesson_id);
                                                                } catch (err) {
                                                                    console.error("❌ Failed to fetch progress details", err);
                                                                    setFatalError(true);
                                                                }
                                                            }}
                                                        >
                                                            {lessonProgress[lesson.lesson_id]
                                                                ? `${Math.round(lessonProgress[lesson.lesson_id].percent)}%`
                                                                : "View Progress"}
                                                        </Button>
                                                    )
                                                ) : (
                                                    <span className="text-sm italic text-gray-400">Draft</span>
                                                )}
                                            </td>

                                            <td className={`px-4 py-3 ${isDraft ? "text-gray-400 italic" : ""}`}>
                                                {lesson.target_user ?? "All Users"}
                                            </td>

                                            <td className="px-4 py-3">
                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="auto"
                                                        onClick={() => setModalContent(lesson)}
                                                        className="p-2"
                                                    >
                                                        <Eye className="w-4 h-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="auto"
                                                        onClick={() => handleEditLesson(lesson)}
                                                        className="p-2"
                                                    >
                                                        <Pencil className="w-4 h-4" />
                                                    </Button>
                                                    <Button
                                                        variant={lesson.published ? "danger" : "success"}
                                                        size="auto"
                                                        onClick={async () => {
                                                            try {
                                                                const updated = await togglePublishLesson(lesson.lesson_id, {
                                                                    ...lesson,
                                                                    published: lesson.published ? 0 : 1,
                                                                });
                                                                if (updated.ok || updated === true) {
                                                                    const refreshed = await getLessons();
                                                                    setLessons(Array.isArray(refreshed) ? refreshed : []);
                                                                }
                                                            } catch (err) {
                                                                console.error("❌ Failed to toggle publish status", err);
                                                                setFatalError(true);
                                                            }
                                                        }}
                                                        className="p-2"
                                                    >
                                                        {lesson.published ? <Ban className="w-4 h-4" /> : <Megaphone className="w-4 h-4" />}
                                                    </Button>
                                                    <Button
                                                        variant="danger"
                                                        size="auto"
                                                        onClick={() => setDeleteModal({ show: true, lesson })}
                                                        className="p-2"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </Button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* User Feedback Section */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <MessageSquare className={`w-6 h-6 ${darkMode ? "text-blue-400" : "text-blue-600"}`} />
                        <h2 className="text-xl font-bold">User Feedback</h2>
                    </div>
                    {supportFeedback.length === 0 ? (
                        <div className="text-center py-8 text-gray-400">
                            <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
                            <p>No feedback messages yet</p>
                        </div>
                    ) : (
                        <div className="space-y-3 max-h-64 overflow-y-auto">
                            {supportFeedback.map((fb) => (
                                <div key={fb.id} className={`p-4 rounded-lg border ${darkMode ? "border-gray-600 bg-gray-700" : "border-gray-200 bg-gray-50"}`}>
                                    <div className="flex justify-between items-start gap-3">
                                        <p className="whitespace-pre-wrap mb-2 flex-1">{fb.message}</p>
                                        <button
                                            onClick={() => handleDeleteFeedback(fb.id)}
                                            className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded ${darkMode ? "bg-red-600/20 text-red-300 hover:bg-red-600/30" : "bg-red-100 text-red-600 hover:bg-red-200"}`}
                                            title="Delete feedback"
                                        >
                                            <Trash2 className="w-3 h-3" /> Delete
                                        </button>
                                    </div>
                                    {fb.created_at && (
                                        <div className="flex items-center gap-2 text-xs text-gray-400">
                                            <Calendar className="w-3 h-3" />
                                            {new Date(fb.created_at).toLocaleString()}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Modals */}
                {modalContent && (
                    <Modal onClose={() => setModalContent(null)}>
                        <div className="flex items-center gap-3 mb-4">
                            <BookOpen className="w-6 h-6 text-blue-500" />
                            <h2 className="text-xl font-bold">{modalContent.title}</h2>
                        </div>
                        <BlockContentRenderer html={modalContent.content} mode="admin-preview" />
                    </Modal>
                )}

                {showEditorModal && (
                    <Modal onClose={() => setShowEditorModal(false)}>
                        <div className="flex items-center gap-3 mb-4">
                            <Pencil className="w-6 h-6 text-blue-500" />
                            <h2 className="text-xl font-bold">
                                {isEditing ? "Edit Lesson" : "Create New Lesson"}
                            </h2>
                        </div>

                        <Input
                            type="number"
                            placeholder="Lesson ID"
                            value={newLessonId}
                            disabled={isEditing}
                            onChange={(e) => setNewLessonId(e.target.value)}
                            className="mb-3"
                        />
                        <Input
                            type="text"
                            placeholder="Lesson Title"
                            value={newTitle}
                            onChange={(e) => setNewTitle(e.target.value)}
                            className="mb-3"
                        />

                        <div className="flex items-center mb-3 gap-2">
                            <label className="flex items-center gap-2 m-0 whitespace-nowrap">
                                <input
                                    type="checkbox"
                                    checked={aiEnabled}
                                    onChange={(e) => setAiEnabled(e.target.checked)}
                                />
                                <span>Include AI Exercises</span>
                            </label>
                        </div>

                        {formError && (
                            <div className="text-red-600 text-sm mb-3 font-medium">{formError}</div>
                        )}

                        <LessonEditor
                            content={newContent}
                            onContentChange={setNewContent}
                            aiEnabled={aiEnabled}
                            onToggleAI={() => setAiEnabled((v) => !v)}
                        />
                        <div className="flex justify-end mt-4 gap-2">
                            <Button variant="secondary" onClick={() => handleSaveLesson(false)} className="gap-2">
                                <Save className="w-4 h-4" />
                                Save as Draft
                            </Button>
                            <Button variant="success" onClick={() => handleSaveLesson(true)} className="gap-2">
                                <Rocket className="w-4 h-4" />
                                Save & Publish
                            </Button>
                        </div>
                    </Modal>
                )}

                {showLessonModal && (
                    <Modal onClose={() => setShowLessonModal(null)}>
                        <div className="flex items-center gap-3 mb-4">
                            <BarChart3 className="w-6 h-6 text-blue-500" />
                            <h2 className="text-xl font-bold">Lesson {showLessonModal} – User Progress</h2>
                        </div>

                        {lessonProgressDetails.length === 0 ? (
                            <div className="text-center py-8 text-gray-400">
                                <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                <p>No progress data available</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {lessonProgressDetails.map((entry, index) => (
                                    <div key={`${entry.user}-${index}`} className={`flex justify-between items-center p-3 rounded-lg ${darkMode ? "bg-gray-700" : "bg-gray-50"}`}>
                                        <span className="font-medium">{entry.user}</span>
                                        <span className="text-sm text-gray-600">{entry.percent}% ({entry.completed}/{entry.total})</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </Modal>
                )}

                {/* Delete Confirmation Modal */}
                {deleteModal.show && deleteModal.lesson && (
                    <Modal onClose={() => setDeleteModal({ show: false, lesson: null })}>
                        <div className="flex items-center gap-3 mb-4">
                            <Trash2 className="w-6 h-6 text-red-500" />
                            <h2 className="text-xl font-bold">Delete Lesson</h2>
                        </div>

                        <div className="mb-6">
                            <p className="text-gray-700 dark:text-gray-300 mb-4">
                                Are you sure you want to delete the lesson <strong className="text-gray-900 dark:text-white">"{deleteModal.lesson.title}"</strong>?
                            </p>
                            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                                <div className="flex items-start gap-3">
                                    <Shield className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
                                    <div>
                                        <p className="text-red-900 dark:text-red-200 font-medium mb-1">This action cannot be undone</p>
                                        <p className="text-red-800 dark:text-red-300 text-sm">
                                            This will permanently delete the lesson and all associated progress data.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end gap-3">
                            <Button
                                variant="secondary"
                                onClick={() => setDeleteModal({ show: false, lesson: null })}
                            >
                                Cancel
                            </Button>
                            <Button
                                variant="danger"
                                onClick={() => handleDeleteLesson(deleteModal.lesson)}
                                className="gap-2"
                            >
                                <Trash2 className="w-4 h-4" />
                                Delete Lesson
                            </Button>
                        </div>
                    </Modal>
                )}

                <Footer />
                    </div>
                </div>
        </Container>
    );
}

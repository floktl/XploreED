import { Link } from "react-router-dom";
import Button from "../../../../common/UI/Button";
import {
    BookOpen,
    Plus,
    Settings,
    Eye,
    Pencil,
    Ban,
    Megaphone,
    Trash2,
    BarChart3,
    Calendar,
    Target
} from "lucide-react";

export default function LessonManagement({
    lessons,
    lessonProgress,
    darkMode,
    setIsEditing,
    setNewLessonId,
    setNewTitle,
    setNewContent,
    setFormError,
    setAiEnabled,
    setShowEditorModal,
    getLessonProgressDetails,
    setLessonProgressDetails,
    setShowLessonModal,
    setFatalError,
    setModalContent,
    handleEditLesson,
    togglePublishLesson,
    getLessons,
    setLessons,
    setDeleteModal
}) {
    return (
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
    );
}

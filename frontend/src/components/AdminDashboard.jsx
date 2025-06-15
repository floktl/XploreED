import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";
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
  const setIsAdmin = useAppStore((state) => state.setIsAdmin);


  const navigate = useNavigate();
  const darkMode = useAppStore((state) => state.darkMode);
  const isAdmin = useAppStore((state) => state.isAdmin);
  const isLoading = useAppStore((state) => state.isLoading);

  if (fatalError) {
    return <ErrorPage />;
  }

  useEffect(() => {
    const verifyAdmin = async () => {
      try {
        const data = await getAdminRole();
        setIsAdmin(data.is_admin);

        if (!data.is_admin) {
          navigate("/admin-login");
          return;
        }

        // ✅ now safe to load data
        const [results, lessons, progress, feedback] = await Promise.all([
          getAdminResults(),
          getLessons(),
          getLessonProgressSummary(),
          fetchSupportFeedback(),
        ]);

        setResults(results);
        setLessons(Array.isArray(lessons) ? lessons : []);
        setLessonProgress(progress);
        setSupportFeedback(Array.isArray(feedback) ? feedback : []);

      } catch (err) {
        console.error("❌ Admin verification failed:", err);
        setFatalError(true);
      }
    };

    verifyAdmin();
  }, [navigate, setIsAdmin]);

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
      setFormError("❗ Please fill out all fields.");
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
      setFormError(`❌ Lesson ID ${newLessonId} already exists. Please choose a different ID.`);
      return;
    }

    if (duplicateTitle) {
      setFormError(`❌ Lesson title "${newTitle}" already exists. Please choose a different title.`);
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
        setFormError("❌ Failed to save lesson.");
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
      setFormError("❌ Could not save lesson.");
      setFatalError(true);
    }
  };
  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>📊 Admin Dashboard</Title>

        {error && <Alert type="danger">{error}</Alert>}

        <Card className="overflow-x-auto mb-10">
          <table className={`min-w-full border rounded-lg ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
            <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
              <tr>
                <th className="px-4 py-2 text-left">User</th>
                <th className="px-4 py-2 text-left">Game Level</th>
                <th className="px-4 py-2 text-left">Last Activity</th>
                <th className="px-4 py-2 text-left">Action</th>
              </tr>
            </thead>
            <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
              {Object.values(userSummary).map((u) => (
                <tr key={u.username} className={darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"}>
                  <td className="px-4 py-2 font-semibold">{u.username}</td>
                  <td className="px-4 py-2">{u.lastLevel ?? "—"}</td>
                  <td className="px-4 py-2">{u.lastTime ? new Date(u.lastTime).toLocaleString() : "—"}</td>
                  <td className="px-4 py-2">
                    <Link to="/profile-stats" state={{ username: u.username }} className="text-blue-600 hover:underline">
                      View Stats →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">📚 All Lessons</h2>
            <Button variant="success" onClick={() => {
              setIsEditing(false);
              setNewLessonId("");
              setNewTitle("");
              setNewContent("");
              setFormError("");
              setAiEnabled(false);
              setShowEditorModal(true);
            }}>
              ➕ Add Lesson
            </Button>
          </div>

          <table className={`min-w-full border rounded-lg overflow-hidden ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
            <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
              <tr>
                <th className="px-4 py-2 text-left">Lesson ID</th>
                <th className="px-4 py-2 text-left">Title</th>
                <th className="px-4 py-2 text-left">Progress</th>
                <th className="px-4 py-2 text-left">Target User</th>
                <th className="px-4 py-2 text-left">Actions</th>
              </tr>
            </thead>
            <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
  {lessons.map((lesson) => {
    const isDraft = lesson.published === 0;

    return (
      <tr key={lesson.lesson_id}>
        <td className={`px-4 py-2 ${isDraft ? "text-gray-400 italic" : ""}`}>
          {lesson.lesson_id}
        </td>
        <td className={`px-4 py-2 ${isDraft ? "text-gray-400 italic" : ""}`}>
          {lesson.title}
        </td>
        <td className={`px-4 py-2 ${isDraft ? "text-gray-400 italic" : ""}`}>
          {lesson.published ? (
            lesson.num_blocks === 0 ? (
              <Button
                variant="outline"
                disabled
                className="opacity-60 cursor-not-allowed"
              >
                🧱
              </Button>
            ) : (
              <Button
                variant="progress"
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
                  : "📊 View"}
              </Button>
            )
          ) : (
            <span className="text-sm italic text-gray-400">Draft</span>
          )}
        </td>

        <td className={`px-4 py-2 ${isDraft ? "text-gray-400 italic" : ""}`}>
          {lesson.target_user ?? "🌍"}
        </td>

        <td className="px-4 py-2 flex gap-2">
          <Button variant="ghost" onClick={() => setModalContent(lesson)}>🔍</Button>
          <Button variant="ghost" onClick={() => handleEditLesson(lesson)}>✏️</Button>
          <Button
            variant={lesson.published ? "danger" : "success"}
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
          >
            {lesson.published ? "🚫" : "📢"}
          </Button>
          <Button
            variant="danger"
            onClick={async () => {
              if (!window.confirm("Are you sure you want to delete this lesson?")) return;
              try {
                const deleted = await deleteLesson(lesson.lesson_id);
                if (deleted.ok || deleted === true) {
                  setLessons((prev) => prev.filter((l) => l.lesson_id !== lesson.lesson_id));
                }
              } catch (err) {
                console.error("❌ Failed to delete lesson", err);
                setFatalError(true);
              }
            }}
          >
            ❌
          </Button>
        </td>
      </tr>
    );
  })}
</tbody>

          </table>
        </Card>

        <Card className="mt-8">
          <h2 className="text-xl font-bold mb-4">📮 User Feedback</h2>
          {supportFeedback.length === 0 ? (
            <p>No feedback messages.</p>
          ) : (
            <ul className="space-y-2 max-h-64 overflow-y-auto">
              {supportFeedback.map((fb) => (
                <li key={fb.id} className="border-b pb-1 last:border-none">
                  <p className="whitespace-pre-wrap">{fb.message}</p>
                  {fb.created_at && (
                    <span className="text-xs text-gray-400">
                      {new Date(fb.created_at).toLocaleString()}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </Container>

      {modalContent && (
        <Modal onClose={() => setModalContent(null)}>
          <h2 className="text-xl font-bold mb-2">📘 {modalContent.title}</h2>
          <BlockContentRenderer html={modalContent.content} mode="admin-preview" />
        </Modal>
      )}

      {showEditorModal && (
        <Modal onClose={() => setShowEditorModal(false)}>
          <h2 className="text-xl font-bold mb-4">
            {isEditing ? "✏️ Edit Lesson" : "📝 Create New Lesson"}
          </h2>
          <input
            type="number"
            placeholder="Lesson ID"
            value={newLessonId}
            disabled={isEditing}
            onChange={(e) => setNewLessonId(e.target.value)}
            className="w-full mb-3 px-3 py-2 rounded border dark:bg-gray-800 dark:text-white"
          />
          <input
            type="text"
            placeholder="Lesson Title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            className="w-full mb-3 px-3 py-2 rounded border dark:bg-gray-800 dark:text-white"
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
            <Button variant="secondary" onClick={() => handleSaveLesson(false)}>
              💾 Save as Draft
            </Button>
            <Button variant="success" onClick={() => handleSaveLesson(true)}>
              🚀 Save & Publish
            </Button>
          </div>
        </Modal>
      )}

      {showLessonModal && (
        <Modal onClose={() => setShowLessonModal(null)}>
          <h2 className="text-xl font-bold mb-4">📘 Lesson {showLessonModal} – User Progress</h2>
          {lessonProgressDetails.length === 0 ? (
            <p>No progress data available.</p>
          ) : (
            <ul className="space-y-2">
              {lessonProgressDetails.map((entry, index) => (
                <li key={`${entry.user}-${index}`} className="flex justify-between">
                  <span className="font-medium">{entry.user}</span>
                  <span>{entry.percent}% ({entry.completed}/{entry.total})</span>
                </li>
              ))}
            </ul>
          )}
        </Modal>
      )}

      <Footer />
    </div>
  );

}

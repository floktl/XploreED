import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import Modal from "./UI/Modal";
import useAppStore from "../store/useAppStore";
import useRequireAdmin from "../hooks/useRequireAdmin";
import LessonEditor from "./LessonEditor";
import BlockContentRenderer from "./BlockContentRenderer";

export default function AdminDashboard() {
  useRequireAdmin();
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");
  const [modalContent, setModalContent] = useState(null);
  const [showEditorModal, setShowEditorModal] = useState(false);
  const [newLessonId, setNewLessonId] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [lessons, setLessons] = useState([]);
  const [lessonProgress, setLessonProgress] = useState({});
  const [showLessonModal, setShowLessonModal] = useState(null);
  const [lessonProgressDetails, setLessonProgressDetails] = useState([]);

  const navigate = useNavigate();
  const darkMode = useAppStore((state) => state.darkMode);
  const isAdmin = useAppStore((state) => state.isAdmin);
  const isLoading = useAppStore((state) => state.isLoading);

  useEffect(() => {
    if (isLoading || !isAdmin) {
      navigate("/admin-login");
    }

    const fetchData = async () => {
      try {
        const [resultsRes, lessonsRes, progressRes] = await Promise.all([
          fetch("http://localhost:5050/api/admin/results", { credentials: "include" }),
          fetch("http://localhost:5050/api/admin/lesson-content", { credentials: "include" }),
          fetch("http://localhost:5050/api/admin/lesson-progress-summary", { credentials: "include" }),
        ]);

        if (resultsRes.ok) setResults(await resultsRes.json());
        if (lessonsRes.ok) setLessons(await lessonsRes.json());
        if (progressRes.ok) setLessonProgress(await progressRes.json());
      } catch (err) {
        console.error("Error fetching data:", err);
        setError("❌ Could not connect to the server.");
      }
    };

    fetchData();
  }, [isAdmin, isLoading, navigate]);

  const userSummary = results.reduce((acc, curr) => {
    const { username, timestamp, level } = curr;
    if (!acc[username] || new Date(timestamp) > new Date(acc[username].lastTime || 0)) {
      acc[username] = { username, lastLevel: level, lastTime: timestamp };
    }
    return acc;
  }, {});

  const handleCreateLesson = async () => {
    if (!newTitle || !newContent || !newLessonId) return;

    try {
      const res = await fetch("http://localhost:5050/api/admin/lesson-content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          lesson_id: parseInt(newLessonId),
          title: newTitle,
          content: newContent,
        }),
      });

      if (res.ok) {
        setShowEditorModal(false);
        setNewLessonId("");
        setNewTitle("");
        setNewContent("");
      } else {
        alert("❌ Failed to create lesson");
      }
    } catch (err) {
      console.error("Error saving lesson:", err);
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
                <th className="px-4 py-2 text-left">Last Level</th>
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
                    <Link
                      to="/profile-stats"
                      state={{ username: u.username }}
                      className="text-blue-600 hover:underline"
                    >
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
            <Button variant="success" onClick={() => setShowEditorModal(true)}>➕ Add Lesson</Button>
          </div>

          <table className={`min-w-full border rounded-lg overflow-hidden ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
            <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
              <tr>
                <th className="px-4 py-2 text-left">Lesson ID</th>
                <th className="px-4 py-2 text-left">Title</th>
                <th className="px-4 py-2 text-left">Avg Progress</th>
                <th className="px-4 py-2 text-left">Target User</th>
                <th className="px-4 py-2 text-left">Actions</th>
              </tr>
            </thead>
            <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
              {lessons.map((lesson) => (
                <tr key={lesson.lesson_id}>
                  <td className="px-4 py-2">{lesson.lesson_id}</td>
                  <td className="px-4 py-2">{lesson.title}</td>
                  <td className="px-4 py-2">
                    <Button
                      variant="info"
                      onClick={async () => {
                        try {
                          const res = await fetch(`http://localhost:5050/api/admin/lesson-progress/${lesson.lesson_id}`, {
                            credentials: "include",
                          });
                          if (res.ok) {
                            const data = await res.json();
                            setLessonProgressDetails(data);
                            setShowLessonModal(lesson.lesson_id);
                          }
                        } catch (err) {
                          console.error("❌ Failed to fetch progress details", err);
                        }
                      }}
                    >
                      {lessonProgress[lesson.lesson_id] !== undefined
                        ? `${Math.round(lessonProgress[lesson.lesson_id])}%`
                        : "📊 View"}
                    </Button>
                  </td>
                  <td className="px-4 py-2">{lesson.target_user ?? "🌍 All Users"}</td>
                  <td className="px-4 py-2 flex gap-2">
                    <Button variant="ghost" onClick={() => setModalContent(lesson)}>🔍 Preview</Button>
                    <Button
                      variant="danger"
                      onClick={async () => {
                        if (!window.confirm("Are you sure you want to delete this lesson?")) return;
                        const res = await fetch(`http://localhost:5050/api/admin/lesson-content/${lesson.lesson_id}`, {
                          method: "DELETE",
                          credentials: "include",
                        });
                        if (res.ok) {
                          setLessons((prev) => prev.filter((l) => l.lesson_id !== lesson.lesson_id));
                        }
                      }}
                    >
                      ❌ Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </Container>

      {modalContent && (
        <Modal onClose={() => setModalContent(null)}>
          <h2 className="text-xl font-bold mb-2">📘 {modalContent.title}</h2>
          <BlockContentRenderer html={modalContent.content} />
        </Modal>
      )}

      {showEditorModal && (
        <Modal onClose={() => setShowEditorModal(false)}>
          <h2 className="text-xl font-bold mb-4">📝 Create New Lesson</h2>
          <input
            type="number"
            placeholder="Lesson ID"
            value={newLessonId}
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
          <LessonEditor content={newContent} onContentChange={setNewContent} />
          <div className="flex justify-end mt-4">
            <Button variant="success" onClick={handleCreateLesson}>💾 Save Lesson</Button>
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

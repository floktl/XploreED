import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getTopicMemory, clearTopicMemory } from "../api";
import Button from "./UI/Button";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import Badge from "./UI/Badge";
import Modal from "./UI/Modal";
import { Container, Title } from "./UI/UI";
import useAppStore from "../store/useAppStore";

export default function TopicMemory() {
  const [topics, setTopics] = useState([]);
  const [showClear, setShowClear] = useState(false);
  const [error, setError] = useState("");
  const username = useAppStore((state) => state.username);
  const setUsername = useAppStore((state) => state.setUsername);
  const darkMode = useAppStore((state) => state.darkMode);
  const isAdmin = useAppStore((state) => state.isAdmin);
  const navigate = useNavigate();
  const isLoading = useAppStore((state) => state.isLoading);

  useEffect(() => {
    const storedUsername = localStorage.getItem("username");
    if (!username && storedUsername) {
      setUsername(storedUsername);
    }

    if (!isLoading && (!username || isAdmin)) {
      navigate(isAdmin ? "/admin-panel" : "/");
    }
  }, [isAdmin, username, setUsername, navigate]);

  useEffect(() => {
    if (!isAdmin) {
      getTopicMemory()
        .then(setTopics)
        .catch((err) => {
          console.error("Failed to load topic memory:", err);
        });
    }
  }, [username, isAdmin]);

  const handleClear = async () => {
    try {
      await clearTopicMemory();
      setTopics([]);
      setShowClear(false);
      setError("");
    } catch (err) {
      console.error("Failed to clear topic memory:", err);
      setError("❌ Could not clear topic memory.");
    }
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>
          🧠 Topic Memory — <span className="text-blue-600">{username || "anonymous"}</span>
          <Badge type="default">Student</Badge>
        </Title>
        <p className={`mb-6 text-center ${darkMode ? "text-gray-300" : "text-gray-600"}`}>Your simulation of your memory</p>

        {topics.length === 0 ? (
          <Alert type="info">No topic memory saved yet.</Alert>
        ) : (
          <Card className="overflow-x-auto">
            <table className={`min-w-full border rounded-lg overflow-hidden ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
              <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
                <tr>
                  <th className="px-4 py-2 text-left">Grammar</th>
                  <th className="px-4 py-2 text-left">Topic</th>
                  <th className="px-4 py-2 text-left">Skill</th>
                  <th className="px-4 py-2 text-left">Context</th>
                  <th className="px-4 py-2 text-left">Ease</th>
                  <th className="px-4 py-2 text-left">Interval</th>
                  <th className="px-4 py-2 text-left">Next</th>
                  <th className="px-4 py-2 text-left">Reps</th>
                </tr>
              </thead>
              <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
                {topics.map((t) => (
                  <tr key={t.id} className={darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"}>
                    <td className="px-4 py-2 font-medium">{t.grammar || "-"}</td>
                    <td className="px-4 py-2">{t.topic || "-"}</td>
                    <td className={`px-4 py-2 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>{t.skill_type}</td>
                    <td className="px-4 py-2 whitespace-nowrap max-w-xs overflow-hidden text-ellipsis">{t.context}</td>
                    <td className="px-4 py-2">{Number(t.ease_factor).toFixed(2)}</td>
                    <td className="px-4 py-2">{t.intervall}</td>
                    <td className="px-4 py-2">{t.next_repeat ? new Date(t.next_repeat).toLocaleDateString() : ""}</td>
                    <td className="px-4 py-2">{t.repetitions}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
        <div className="mt-6 flex justify-center gap-4">
          <Button variant="danger" size="md" onClick={() => setShowClear(true)}>
            🗑️ Clear Memory
          </Button>
          <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")}>🔙 Back to Menu</Button>
        </div>
      </Container>
      <Footer />
      {showClear && (
        <Modal onClose={() => setShowClear(false)}>
          <h2 className="text-lg font-bold mb-2">Delete Topic Memory</h2>
          <p className="mb-4">Are you sure you want to delete all saved topic memory?</p>
          {error && <Alert type="error" className="mb-2">{error}</Alert>}
          <div className="flex justify-end gap-2">
            <Button variant="danger" onClick={handleClear}>Delete</Button>
            <Button variant="secondary" onClick={() => setShowClear(false)}>
              Cancel
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}

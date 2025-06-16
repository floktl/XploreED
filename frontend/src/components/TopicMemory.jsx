import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getTopicMemory } from "../api";
import Button from "./UI/Button";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import Badge from "./UI/Badge";
import { Container, Title } from "./UI/UI";
import useAppStore from "../store/useAppStore";

export default function TopicMemory() {
  const [topics, setTopics] = useState([]);
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
                  <th className="px-4 py-2 text-left">Topic</th>
                  <th className="px-4 py-2 text-left">Skill</th>
                  <th className="px-4 py-2 text-left">Ease</th>
                  <th className="px-4 py-2 text-left">Interval</th>
                  <th className="px-4 py-2 text-left">Next</th>
                  <th className="px-4 py-2 text-left">Reps</th>
                </tr>
              </thead>
              <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
                {topics.map((t) => (
                  <tr key={t.id} className={darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"}>
                    <td className="px-4 py-2 font-medium">{t.topic}</td>
                    <td className={`px-4 py-2 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>{t.skill_type}</td>
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

        <div className="mt-6 text-center">
          <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")}>🔙 Back to Menu</Button>
        </div>
      </Container>
      <Footer />
    </div>
  );
}

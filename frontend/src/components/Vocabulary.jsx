import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import Badge from "./UI/Badge";
import Modal from "./UI/Modal";
import { getVocabulary } from "../api";
import useAppStore from "../store/useAppStore";

export default function Vocabulary() {
  const [vocab, setVocab] = useState([]);
  const [selected, setSelected] = useState(null);
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
      getVocabulary()
        .then(setVocab)
        .catch((err) => {
          console.error("Failed to load vocabulary:", err);
        });
    }
  }, [username, isAdmin]);

  return (
    <div
      className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}
    >
      <Container>
        <Title>
          📖 Your Vocabulary —{" "}
          <span className="text-blue-600">{username || "anonymous"}</span>
          <Badge type="default">Student</Badge>
        </Title>

        <p
          className={`mb-6 text-center ${darkMode ? "text-gray-300" : "text-gray-600"}`}
        >
          All words saved from your translations
        </p>

        <div className="mb-4 text-center">
          <Button onClick={() => navigate("/vocab-trainer")}>
            🎯 Train Vocabulary
          </Button>
        </div>

        {vocab.length === 0 ? (
          <Alert type="info">
            🤓 No vocabulary saved yet. Try completing a few translations or
            levels!
          </Alert>
        ) : (
          <Card className="overflow-x-auto">
            <table
              className={`min-w-full border rounded-lg overflow-hidden ${
                darkMode ? "border-gray-600" : "border-gray-200"
              }`}
            >
              <thead
                className={
                  darkMode
                    ? "bg-gray-700 text-gray-200"
                    : "bg-blue-50 text-blue-700"
                }
              >
                <tr>
                  <th className="px-4 py-2 text-left">German Word</th>
                  <th className="px-4 py-2 text-left">English Translation</th>
                  <th className="px-4 py-2 text-left">Due</th>
                </tr>
              </thead>
              <tbody
                className={
                  darkMode
                    ? "bg-gray-900 divide-gray-700"
                    : "bg-white divide-gray-200"
                }
              >
                {vocab.map((v, i) => (
                  <tr
                    key={i}
                    className={
                      darkMode
                        ? "hover:bg-gray-700 cursor-pointer"
                        : "hover:bg-gray-50 cursor-pointer"
                    }
                    onClick={() => setSelected(v)}
                  >
                    <td className="px-4 py-2 font-medium">{v.vocab}</td>
                    <td
                      className={`px-4 py-2 ${darkMode ? "text-gray-300" : "text-gray-600"}`}
                    >
                      {v.translation}
                    </td>
                    <td className="px-4 py-2">
                      {v.next_review
                        ? new Date(v.next_review).toLocaleDateString()
                        : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}

        <div className="mt-6 text-center">
          <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")}>
            🔙 Back to Menu
          </Button>
        </div>
      </Container>
      <Footer />
      {selected && (
        <Modal onClose={() => setSelected(null)}>
          <h2 className="text-xl font-semibold mb-4">{selected.vocab}</h2>
          <p className="mb-2">
            <strong>Translation:</strong> {selected.translation}
          </p>
          {selected.created_at && (
            <p className="mb-2">
              <strong>Learned:</strong>{" "}
              {new Date(selected.created_at).toLocaleString()}
            </p>
          )}
          {selected.context && (
            <p className="mb-2">
              <strong>Context:</strong> {selected.context}
            </p>
          )}
          {selected.exercise && (
            <p className="mb-2">
              <strong>Exercise:</strong> {selected.exercise}
            </p>
          )}
        </Modal>
      )}
    </div>
  );
}

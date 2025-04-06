import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Input, Title, Container } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Spinner from "./UI/Spinner";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";

export default function Translator() {
  const [english, setEnglish] = useState("");
  const [german, setGerman] = useState("");
  const [feedback, setFeedback] = useState("");
  const [studentInput, setStudentInput] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const username = useAppStore((state) => state.username);
  const setUsername = useAppStore((state) => state.setUsername);
  const darkMode = useAppStore((state) => state.darkMode);
  const isAdmin = useAppStore((state) => state.isAdmin);
  const navigate = useNavigate();

  useEffect(() => {
    if (isAdmin) {
      alert("❌ Admins cannot use student translation practice.");
      navigate("/admin-panel");
    }

    const storedUsername = localStorage.getItem("username");
    if (storedUsername && !username) {
      setUsername(storedUsername);
    }
  }, [isAdmin, username, setUsername, navigate]);

  const handleTranslate = async () => {
    setError("");

    if (!english.trim() || !studentInput.trim()) {
      setError("⚠️ Please fill out both fields before submitting.");
      return;
    }

    const payload = {
      english: String(english),
      student_input: String(studentInput),
      username: String(username || "anonymous"),
    };

    try {
      setLoading(true);
      const res = await fetch("http://localhost:5000/api/translate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorText = await res.text();
        console.error("[CLIENT] Server error response:", errorText);
        throw new Error(`❌ Server error: ${res.status}`);
      }

      const data = await res.json();
      setGerman(data.german || "");
      setFeedback(data.feedback || "");
    } catch (err) {
      console.error("[CLIENT] Translation request failed:", err);
      setError("❌ Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setEnglish("");
    setStudentInput("");
    setGerman("");
    setFeedback("");
    setError("");
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>📝 Translation Practice</Title>

        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            handleTranslate();
          }}
        >
          <Input
            autoFocus
            placeholder="Type your English sentence..."
            value={english}
            onChange={(e) => setEnglish(e.target.value)}
          />

          <Input
            placeholder="Your German translation"
            value={studentInput}
            onChange={(e) => setStudentInput(e.target.value)}
          />

          {error && <Alert type="warning">{error}</Alert>}
          {loading && <Spinner />}

          <div className="flex flex-col sm:flex-row gap-3 mt-2">
            <Button type="primary" className="w-full" onClick={handleTranslate} disabled={loading}>
              🚀 {loading ? "Translating..." : "Get Feedback"}
            </Button>
            <Button type="link" className="w-full" onClick={() => navigate("/menu")}>
              ⬅️ Back to Menu
            </Button>
          </div>
        </form>

        {german && (
          <>
            <Card className="mt-8">
              <p className={`text-lg font-semibold mb-2 ${darkMode ? "text-gray-100" : "text-blue-800"}`}>
                🗣️ Correct German:
              </p>
              <p className={`mb-3 ${darkMode ? "text-gray-200" : "text-gray-900"}`}>{german}</p>
              <div
                className={`text-sm ${darkMode ? "text-gray-300" : "text-gray-700"}`}
                dangerouslySetInnerHTML={{ __html: feedback }}
              />
            </Card>

            <div className="mt-6 text-center">
              <Button type="secondary" onClick={handleReset}>
                🆕 New Sentence
              </Button>
            </div>
          </>
        )}
      </Container>

      <Footer />
    </div>
  );
}

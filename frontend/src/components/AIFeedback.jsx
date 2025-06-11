import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";
import useAppStore from "../store/useAppStore";
// import your AI feedback API helper here

export default function AIFeedback() {
  const [feedback, setFeedback] = useState([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const darkMode = useAppStore((state) => state.darkMode);
  const username = useAppStore((state) => state.username);
  const isLoading = useAppStore((state) => state.isLoading);
  const isAdmin = useAppStore((state) => state.isAdmin);

  useEffect(() => {
    if (!isLoading && (!username || isAdmin)) {
      navigate(isAdmin ? "/admin-panel" : "/");
    }
  }, [username, isLoading, isAdmin, navigate]);

  // For demo: read from localStorage
  useEffect(() => {
    try {
      const data = JSON.parse(localStorage.getItem("aiFeedback") || "[]");
      setFeedback(data);
    } catch (err) {
      setError("❌ Could not load AI feedback.");
    }
  }, []);

  return (
    <div
      className={`relative min-h-screen pb-20 ${
        darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"
      }`}
    >
      <Container>
        <Title>🤖 {username}'s AI Lessons</Title>
        <p
          className={`text-center mb-6 ${
            darkMode ? "text-gray-300" : "text-gray-600"
          }`}
        >
          Here is your personalized feedback from our AI
        </p>
        {error && <Alert type="danger">{error}</Alert>}
        {feedback.length === 0 && !error ? (
          <Alert type="info">
            No feedback yet. Complete some lessons to get AI feedback!
          </Alert>
        ) : (
          <div className="flex flex-col gap-4">
            {feedback.map((item, idx) => (
              <Card key={item.id}>
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-semibold">
                      {item.title || `Feedback #${item.id}`}
                    </h3>
                    <p className="text-xs text-gray-400">
                      {item.created_at &&
                        `Created: ${new Date(
                          item.created_at
                        ).toLocaleString()}`}
                    </p>
                  </div>
                  <Button
                    variant="progress"
                    type="button"
                    onClick={() => navigate(`/ai-feedback/${item.id}`)}
                  >
                    View
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
        <div className="mt-6 text-center">
          <Button
            variant="link"
            type="button"
            onClick={() => navigate("/menu")}
          >
            ⬅️ Back to Menu
          </Button>
        </div>
      </Container>
      <Footer />
    </div>
  );
}

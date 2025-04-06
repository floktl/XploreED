import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";

export default function NameInput() {
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const setUsername = useAppStore((state) => state.setUsername);
  const darkMode = useAppStore((state) => state.darkMode);

  const handleContinue = () => {
    if (!name.trim()) {
      setError("⚠️ Please enter a valid name.");
      return;
    }

    const trimmed = name.trim();
    localStorage.setItem("username", trimmed);
    setUsername(trimmed);
    navigate("/menu");
  };

  const handleAdminRedirect = () => {
    navigate("/admin"); // 👉 Go to the dedicated AdminLogin page
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>🎓 Willkommen!</Title>

        <p className={`text-center mb-6 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>
          Please enter your name to begin:
        </p>

        <Card>
          <div className="space-y-4">
            <Input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
            />

            {error && <Alert type="warning">{error}</Alert>}

            <div className="flex flex-col sm:flex-row sm:space-x-4 space-y-2 sm:space-y-0">
              <Button type="primary" onClick={handleContinue} className="w-full sm:w-auto">
                🚀 Continue
              </Button>
              <Button type="secondary" onClick={handleAdminRedirect} className="w-full sm:w-auto">
                🔐 Admin Login
              </Button>
            </div>
          </div>
        </Card>
      </Container>

      <Footer />
    </div>
  );
}

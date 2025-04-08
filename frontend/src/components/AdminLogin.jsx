import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";

export default function AdminLogin() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const darkMode = useAppStore((state) => state.darkMode);
  const setIsAdmin = useAppStore((state) => state.setIsAdmin);

  const handleLogin = async () => {
    try {
      const res = await fetch("http://localhost:5050/api/admin/login", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ password }),
      });

      if (res.ok) {
        setIsAdmin(true);
        navigate("/admin-panel");
      } else {
        const data = await res.json();
        setError(data.error || "❌ Login failed.");
      }
    } catch (err) {
      console.error("[CLIENT] Login failed:", err);
      setError("❌ Server error. Please try again.");
    }
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>🔐 Admin Login</Title>

        <Card>
          <div className="space-y-4">
            <Input
              type="password"
              placeholder="Enter Admin Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            {error && <Alert type="error">{error}</Alert>}

            <Button onClick={handleLogin} variant="primary" type="submit" className="w-full">
              🔓 Login
            </Button>

            <Button onClick={() => navigate("/")} variant="link" type="submit" className="w-full">
              ⬅️ Back to Student Login
            </Button>
          </div>
        </Card>
      </Container>

      <Footer />
    </div>
  );
}

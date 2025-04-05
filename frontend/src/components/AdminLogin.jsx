import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import { verifyAdminPassword } from "../api";
import useAppStore from "../store/useAppStore";

export default function AdminLogin() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const setUsername = useAppStore((state) => state.setUsername);
  const darkMode = useAppStore((state) => state.darkMode);

  const setAdminPassword = useAppStore((state) => state.setAdminPassword);

  const handleLogin = async () => {
    const isValid = await verifyAdminPassword(password);
    if (isValid) {
      setUsername("admin");
      setAdminPassword(password); // ✅ store it globally
      navigate("/admin-panel");
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

            <Button onClick={handleLogin} type="primary" className="w-full">
              🔓 Login
            </Button>

            <Button onClick={() => navigate("/menu")} type="link" className="w-full">
              ⬅️ Back to Menu
            </Button>
          </div>
        </Card>
      </Container>

      <Footer />
    </div>
  );
}

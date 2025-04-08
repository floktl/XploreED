import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";
import { login, signup, getMe, getRole } from "../api";

export default function NameInput() {
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const navigate = useNavigate();

  const setUsername = useAppStore((state) => state.setUsername);
  const setIsAdmin = useAppStore((state) => state.setIsAdmin);
  const darkMode = useAppStore((state) => state.darkMode);

  const handleSubmit = async () => {
    const trimmed = name.trim();
    const pw = password.trim();
    const pwConfirm = confirmPassword.trim();

    if (!trimmed || !pw || (isSignup && !pwConfirm)) {
      setError("⚠️ Please fill out all fields.");
      return;
    }

    if (isSignup && pw !== pwConfirm) {
      setError("❌ Passwords do not match.");
      return;
    }

    try {
      let res;
      if (isSignup) {
        res = await signup(trimmed, pw);
        if (res.error) throw new Error(res.error);
        res = await login(trimmed, pw);
        if (res.error) throw new Error(res.error);
      } else {
        res = await login(trimmed, pw);
        if (res.error) throw new Error(res.error);
      }

      const me = await getMe();
      const role = await getRole();

      setUsername(me.username);
      setIsAdmin(role.is_admin);
      localStorage.setItem("username", me.username);
      navigate("/menu");
    } catch (err) {
      console.error("[CLIENT] Auth failed:", err);
      setError("❌ " + (err.message || "Could not log in. Try again."));
    }
  };

  const handleAdminRedirect = () => navigate("/admin");

  const getPasswordStrength = (pw) => {
    if (!pw) return "";
    if (pw.length < 6) return "Weak 🔴";
    if (pw.match(/[A-Z]/) && pw.match(/[0-9]/) && pw.length >= 8) return "Strong 🟢";
    return "Moderate 🟡";
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>{isSignup ? "👋 Create an Account" : "🎓 Willkommen!"}</Title>
        <p className={`text-center mb-6 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>
          {isSignup ? "Choose your username and password." : "Please enter your name and password to begin:"}
        </p>

        <Card>
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
            <Input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
            />

            <div className="relative">
              <Input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
              />
              <span
                className="absolute right-3 top-2 text-xl cursor-pointer select-none"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? "🙈" : "👁️"}
              </span>
              {isSignup && password && (
                <p className="text-sm mt-1 text-gray-500 italic">
                  Strength: {getPasswordStrength(password)}
                </p>
              )}
            </div>

            {isSignup && (
              <Input
                type={showPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat your password"
              />
            )}

            {error && <Alert type="warning">{error}</Alert>}

            <div className="flex flex-col sm:flex-row sm:space-x-4 space-y-2 sm:space-y-0">
              <Button variant="primary" type="submit" className="w-full sm:w-auto">
                {isSignup ? "📝 Sign Up" : "🚀 Continue"}
              </Button>
              <Button variant="secondary" type="button" onClick={handleAdminRedirect} className="w-full sm:w-auto">
                🔐 Admin Login
              </Button>
            </div>

            <div className="text-center pt-2 text-sm">
              {isSignup ? (
                <>
                  Already have an account?{" "}
                  <button type="button" onClick={() => setIsSignup(false)} className="text-blue-500 underline">
                    Log in
                  </button>
                </>
              ) : (
                <>
                  Don't have an account?{" "}
                  <button type="button" onClick={() => setIsSignup(true)} className="text-blue-500 underline">
                    Sign up
                  </button>
                </>
              )}
            </div>
          </form>
        </Card>
      </Container>
      <Footer />
    </div>
  );
}

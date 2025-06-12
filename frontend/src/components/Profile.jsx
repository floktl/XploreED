import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Badge from "./UI/Badge";
import Footer from "./UI/Footer";
import { getMe, getRole, fetchProfileResults } from "../api";
import useAppStore from "../store/useAppStore";

export default function Profile() {
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  const username = useAppStore((state) => state.username);
  const setUsername = useAppStore((state) => state.setUsername);
  const isAdmin = useAppStore((state) => state.isAdmin);
  const setIsAdmin = useAppStore((state) => state.setIsAdmin);
  const navigate = useNavigate();
  const darkMode = useAppStore((state) => state.darkMode);
  const toggleDarkMode = useAppStore((state) => state.toggleDarkMode);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const data = await getMe();
        setUsername(data.username);
  
        const roleData = await getRole();
        setIsAdmin(roleData.is_admin);
  
        if (roleData.is_admin) {
          navigate("/admin-panel");
          return;
        }
  
        const profileResults = await fetchProfileResults();
        setResults(profileResults);
      } catch (err) {
        console.warn("[CLIENT] Not logged in or session expired.");
        navigate("/");
      }
    };
  
    checkSession();
  }, [navigate, setUsername, setIsAdmin]);
  
  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>
          👤 Profile {username && `(${username})`} <Badge type="default">Student</Badge>
        </Title>
        <p className={`text-center mb-6 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>
          📚 Your game results are listed below:
        </p>

        {error && <Alert type="error">{error}</Alert>}

        {!error && results.length === 0 ? (
          <Alert type="info">
            No results yet! Try completing a translation or a game level.
          </Alert>
        ) : (
          <Card className="overflow-x-auto">
            <table className={`min-w-full border rounded-lg overflow-hidden ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
              <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
                <tr>
                  <th className="px-4 py-2 text-left">Level</th>
                  <th className="px-4 py-2 text-left">Correct</th>
                  <th className="px-4 py-2 text-left">Your Answer</th>
                  <th className="px-4 py-2 text-left">Time</th>
                </tr>
              </thead>
              <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
                {results.map((r, i) => (
                  <tr key={i} className={darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"}>
                    <td className="px-4 py-2 font-medium">{r.level === -1 ? "Free" : r.level}</td>
                    <td className="px-4 py-2">
                      <Badge type={r.correct ? "success" : "error"}>
                        {r.correct ? "✅" : "❌"}
                      </Badge>
                    </td>
                    <td className={`px-4 py-2 ${darkMode ? "text-gray-300" : "text-gray-700"}`}>{r.answer}</td>
                    <td className={`px-4 py-2 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>{new Date(r.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}

        <div className="mt-6 flex justify-center gap-4">
          <Button onClick={() => navigate("/settings")}>⚙️ Settings</Button>
          <Button variant="secondary" onClick={toggleDarkMode}>
            {darkMode ? "☀️ Light" : "🌙 Dark"}
          </Button>
          <Button onClick={() => navigate("/menu")} variant="link">
            ⬅️ Back to Menu
          </Button>
        </div>
      </Container>

      <Footer />
    </div>
  );
}

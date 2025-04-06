import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Badge from "./UI/Badge";
import Footer from "./UI/Footer";
import { fetchProfileResults } from "../api";
import useAppStore from "../store/useAppStore";

export default function Profile() {
  const [results, setResults] = useState([]);
  const username = useAppStore((state) => state.username);
  const setUsername = useAppStore((state) => state.setUsername);
  const darkMode = useAppStore((state) => state.darkMode);
  const isAdmin = useAppStore((state) => state.isAdmin);
  const navigate = useNavigate();

  useEffect(() => {
    if (isAdmin) {
      navigate("/admin-panel");
      return;
    }

    const storedUsername = localStorage.getItem("username");
    if (storedUsername && !username) {
      setUsername(storedUsername);
    }
  }, [isAdmin, username, setUsername, navigate]);

  useEffect(() => {
    if (!isAdmin && username) {
      fetchProfileResults(username).then(setResults);
    }
  }, [username, isAdmin]);

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>
          👤 Profile: {username || "anonymous"}
          <Badge type="default">Student</Badge>
        </Title>
        <p className={`text-center mb-6 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>
          📚 Your game results are listed below:
        </p>

        {results.length === 0 ? (
          <Alert type="info">
            No results yet! Try completing a translation or a game level.
          </Alert>
        ) : (
          <Card className="overflow-x-auto">
            <table className={`min-w-full border rounded-lg overflow-hidden ${
              darkMode ? "border-gray-600" : "border-gray-200"
            }`}>
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
                    <td className="px-4 py-2 font-medium">
                      {r.level === -1 ? "Free" : r.level}
                    </td>
                    <td className="px-4 py-2">
                      <Badge type={r.correct ? "success" : "error"}>
                        {r.correct ? "✅" : "❌"}
                      </Badge>
                    </td>
                    <td className={`px-4 py-2 ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
                      {r.answer}
                    </td>
                    <td className={`px-4 py-2 ${darkMode ? "text-gray-400" : "text-gray-500"}`}>
                      {new Date(r.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}

        <div className="mt-6 text-center">
          <Button type="link" onClick={() => navigate("/menu")}>
            ⬅️ Back to Menu
          </Button>
        </div>
      </Container>

      <Footer />
    </div>
  );
}

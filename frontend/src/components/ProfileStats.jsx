import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { fetchProfileStats } from "../api";
import useAppStore from "../store/useAppStore";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Button from "./UI/Button";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";

export default function ProfileStats() {
  const { username } = useParams();
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  const darkMode = useAppStore((s) => s.darkMode);
  const adminPassword = useAppStore((s) => s.adminPassword);
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchProfileStats(username, adminPassword);
        setResults(data);
      } catch (err) {
        setError(err.message || "Could not load profile stats.");
      }
    };

    load();
  }, [username, adminPassword]);

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>📊 Stats for: {username}</Title>

        {error && <Alert type="error">{error}</Alert>}

        {results.length === 0 ? (
          <Alert type="info">No data found.</Alert>
        ) : (
          <Card className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr>
                  <th className="px-4 py-2 text-left">Level</th>
                  <th className="px-4 py-2 text-left">Correct</th>
                  <th className="px-4 py-2 text-left">Answer</th>
                  <th className="px-4 py-2 text-left">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => (
                  <tr key={i}>
                    <td className="px-4 py-2">{r.level}</td>
                    <td className="px-4 py-2">{r.correct ? "✅" : "❌"}</td>
                    <td className="px-4 py-2">{r.answer}</td>
                    <td className="px-4 py-2">{new Date(r.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}

        <div className="mt-6 text-center">
          <Button onClick={() => navigate("/admin-panel")} type="link">
            ⬅️ Back to Admin Panel
          </Button>
        </div>
      </Container>

      <Footer />
    </div>
  );
}

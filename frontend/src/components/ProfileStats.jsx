import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import useAppStore from "../store/useAppStore";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import { ArrowLeft, CheckCircle, XCircle } from "lucide-react";
import Button from "./UI/Button";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";
import { fetchProfileStats } from "../api";

export default function ProfileStats() {
  const navigate = useNavigate();
  const location = useLocation();
  const darkMode = useAppStore((s) => s.darkMode);
  const isAdmin = useAppStore((s) => s.isAdmin);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");
  const username = location.state?.username;

  useEffect(() => {
    if (!isAdmin) {
      console.warn("Access denied: not admin");
      navigate("/admin-login");
      return;
    }

    if (!username) {
      setError("No username provided.");
      return;
    }

    const loadStats = async () => {
      try {
        const data = await fetchProfileStats(username);
        setResults(data);
      } catch (err) {
        console.error("[CLIENT] Failed to load stats:", err);
        setError("Could not load profile stats.");
        navigate("/admin-login");
      }
    };
    

    loadStats();
  }, [username, isAdmin, navigate]);

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container
        bottom={
          <Button onClick={() => navigate("/admin-panel")} variant="link" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Admin Panel
          </Button>
        }
      >
        <Title>📊 Stats for: {username || "—"}</Title>

        {error && <Alert type="error">{error}</Alert>}

        {!error && results.length === 0 ? (
          <Alert type="info">No data found.</Alert>
        ) : (
          <Card fit className="overflow-x-auto">
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
                    <td className="px-4 py-2">
                      {r.correct ? (
                        <CheckCircle className="w-4 h-4 text-green-600" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-600" />
                      )}
                    </td>
                    <td className="px-4 py-2">{r.answer}</td>
                    <td className="px-4 py-2">{new Date(r.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}

      </Container>
      <Footer>
        <Button onClick={() => navigate("/admin-panel")} variant="link" className="gap-2">
          <ArrowLeft className="w-4 h-4" />
          Back to Admin Panel
        </Button>
      </Footer>
    </div>
  );
}
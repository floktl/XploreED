import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Container, Title } from "./UI/UI";
import Footer from "./UI/Footer";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Alert from "./UI/Alert";

export default function ProfileStats() {
  const { username } = useParams();
  const [data, setData] = useState([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`http://localhost:5000/api/profile/${username}`)
      .then((res) => res.json())
      .then(setData)
      .catch(() => setError("❌ Failed to load profile data."));
  }, [username]);

  return (
    <div className="min-h-screen pb-20 bg-gray-100">
      <Container>
        <Title>📈 Stats for {username}</Title>

        {error ? (
          <Alert type="danger">{error}</Alert>
        ) : data.length === 0 ? (
          <Alert type="info">No activity recorded for this user.</Alert>
        ) : (
          <Card>
            <table className="min-w-full">
              <thead>
                <tr>
                  <th className="text-left px-4 py-2">Level</th>
                  <th className="text-left px-4 py-2">Correct</th>
                  <th className="text-left px-4 py-2">Answer</th>
                  <th className="text-left px-4 py-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {data.map((entry, i) => (
                  <tr key={i}>
                    <td className="px-4 py-2">{entry.level}</td>
                    <td className="px-4 py-2">{entry.correct ? "✅" : "❌"}</td>
                    <td className="px-4 py-2">{entry.answer}</td>
                    <td className="px-4 py-2">
                      {new Date(entry.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}

        <div className="mt-6 text-center">
          <Button onClick={() => navigate("/admin-panel")}>⬅️ Back</Button>
        </div>
      </Container>
      <Footer />
    </div>
  );
}

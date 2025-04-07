import React, { useEffect, useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";
import { getAdminResults } from "../api";

export default function AdminDashboard() {
  const [results, setResults] = useState([]);
  const navigate = useNavigate();
  const { state } = useLocation();
  const darkMode = useAppStore((state) => state.darkMode);
  const passwordFromStore = useAppStore((state) => state.adminPassword);
  const isAdmin = useAppStore((state) => state.isAdmin);

  useEffect(() => {
    if (!isAdmin) {
      alert("❌ You must login as admin.");
      navigate("/admin-login");
      return;
    }

    const fetchData = async () => {
      try {
        const res = await getAdminResults(passwordFromStore);
        if (res.ok) {
          const data = await res.json();
          setResults(data);
        } else {
          alert("❌ Unauthorized or failed to load data.");
        }
      } catch (err) {
        console.error("Error loading admin data:", err);
      }
    };

    fetchData();
  }, [isAdmin, navigate, passwordFromStore]);

  const userSummary = results.reduce((acc, curr) => {
    const { username, timestamp, level } = curr;
    if (!acc[username]) {
      acc[username] = { username, lastLevel: level, lastTime: timestamp };
    } else {
      const prevTime = new Date(acc[username].lastTime);
      const currTime = new Date(timestamp);
      if (currTime > prevTime) {
        acc[username].lastTime = timestamp;
        acc[username].lastLevel = level;
      }
    }
    return acc;
  }, {});

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>📊 Admin Dashboard</Title>

        {results.length === 0 ? (
          <Alert type="info">No results found.</Alert>
        ) : (
          <Card className="overflow-x-auto">
            <table className={`min-w-full border rounded-lg overflow-hidden ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
              <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
                <tr>
                  <th className="px-4 py-2 text-left">User</th>
                  <th className="px-4 py-2 text-left">Last Level</th>
                  <th className="px-4 py-2 text-left">Last Activity</th>
                  <th className="px-4 py-2 text-left">Action</th>
                </tr>
              </thead>
              <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
                {Object.values(userSummary).map((u) => (
                  <tr key={u.username} className={darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"}>
                    <td className="px-4 py-2 font-semibold">{u.username}</td>
                    <td className="px-4 py-2">{u.lastLevel}</td>
                    <td className="px-4 py-2">{new Date(u.lastTime).toLocaleString()}</td>
                    <td className="px-4 py-2">
                      <Link to={`/profile-stats/${u.username}`} className="text-blue-600 hover:underline">
                        View Stats →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}

        {/* ✅ Admin Lesson Creation Form */}
        <Card className="mt-10">
          <h2 className="text-xl font-bold mb-4">📘 Add Lesson Content</h2>
          <form
            className="flex flex-col gap-4"
            onSubmit={async (e) => {
              e.preventDefault();
              const lesson_id = e.target.lesson_id.value;
              const title = e.target.title.value;
              const content = e.target.content.value;
              const target_user = e.target.target_user.value;
              const is_public = e.target.public.checked;

              try {
                const res = await fetch("http://localhost:5050/api/admin/lesson-content", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    password: passwordFromStore,
                    lesson_id: parseInt(lesson_id),
                    title,
                    content,
                    target_user: is_public ? null : target_user,
                  }),
                });

                if (res.ok) {
                  alert("✅ Lesson content added successfully!");
                  e.target.reset();
                } else {
                  const err = await res.json();
                  alert("❌ Failed to add lesson content: " + (err.error || "Unknown error"));
                }
              } catch (err) {
                alert("❌ Error while sending data.");
                console.error(err);
              }
            }}
          >
            <div>
              <label className="block font-medium mb-1">Lesson Number</label>
              <input
                type="number"
                name="lesson_id"
                min="0"
                className="w-full px-3 py-2 rounded border dark:bg-gray-800 dark:text-white"
                required
              />
            </div>

            <div>
              <label className="block font-medium mb-1">Title</label>
              <input
                type="text"
                name="title"
                className="w-full px-3 py-2 rounded border dark:bg-gray-800 dark:text-white"
                required
              />
            </div>

            <div>
              <label className="block font-medium mb-1">Lesson Content</label>
              <textarea
                name="content"
                rows="5"
                className="w-full px-3 py-2 rounded border dark:bg-gray-800 dark:text-white"
                required
              />
            </div>

            <div>
              <label className="block font-medium mb-1">Target User (optional)</label>
              <input
                type="text"
                name="target_user"
                className="w-full px-3 py-2 rounded border dark:bg-gray-800 dark:text-white"
                placeholder="Leave empty to publish for everyone"
              />
            </div>

            <div className="flex items-center gap-2">
              <input type="checkbox" name="public" id="public" className="h-4 w-4" />
              <label htmlFor="public">Publish for all users</label>
            </div>

            <Button type="success" className="self-start">
              ➕ Add Content
            </Button>
          </form>
        </Card>
      </Container>

      <Footer />
    </div>
  );
}

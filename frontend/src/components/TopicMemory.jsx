import React, { useEffect, useState } from "react";
import ProgressRing from "./UI/ProgressRing";
import { useNavigate } from "react-router-dom";
import { getTopicMemory, clearTopicMemory } from "../api";
import Button from "./UI/Button";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import Badge from "./UI/Badge";
import Modal from "./UI/Modal";
import { Container, Title, Input } from "./UI/UI";
import useAppStore from "../store/useAppStore";

export default function TopicMemory() {
    const [topics, setTopics] = useState([]);
    const [showClear, setShowClear] = useState(false);
    const [error, setError] = useState("");
    const [weakness, setWeakness] = useState({ grammar: "", percent: 0 });
    const [filters, setFilters] = useState({
        grammar: "",
        topic: "",
        skill: "",
        context: "",
    });
    const username = useAppStore((state) => state.username);
    const setUsername = useAppStore((state) => state.setUsername);
    const darkMode = useAppStore((state) => state.darkMode);
    const isAdmin = useAppStore((state) => state.isAdmin);
    const navigate = useNavigate();
    const isLoading = useAppStore((state) => state.isLoading);

    useEffect(() => {
        const storedUsername = localStorage.getItem("username");
        if (!username && storedUsername) {
            setUsername(storedUsername);
        }

        if (!isLoading && (!username || isAdmin)) {
            navigate(isAdmin ? "/admin-panel" : "/");
        }
    }, [isAdmin, username, setUsername, navigate]);

    useEffect(() => {
        if (!isAdmin) {
            getTopicMemory()
                .then(setTopics)
                .catch((err) => {
                    console.error("Failed to load topic memory:", err);
                });
        }
    }, [username, isAdmin]);

    useEffect(() => {
        if (!topics.length) return;
        const scores = {};
        topics.forEach((t) => {
            const g = t.grammar || "unknown";
            const q = Number(t.quality) || 0;
            if (!scores[g]) scores[g] = { sum: 0, count: 0 };
            scores[g].sum += q;
            scores[g].count += 1;
        });
        let max = -1;
        let worst = "";
        Object.entries(scores).forEach(([g, { sum, count }]) => {
            const avg = sum / count;
            const percent = Math.round((1 - avg / 5) * 100);
            if (percent > max) {
                max = percent;
                worst = g;
            }
        });
        setWeakness({ grammar: worst, percent: max });
    }, [topics]);

    const handleClear = async () => {
        try {
            await clearTopicMemory();
            setTopics([]);
            setShowClear(false);
            setError("");
        } catch (err) {
            console.error("Failed to clear topic memory:", err);
            setError("❌ Could not clear topic memory.");
        }
    };

    const filteredTopics = topics.filter((t) =>
        (t.grammar || "").toLowerCase().includes(filters.grammar.toLowerCase()) &&
        (t.topic || "").toLowerCase().includes(filters.topic.toLowerCase()) &&
        (t.skill_type || "").toLowerCase().includes(filters.skill.toLowerCase()) &&
        (t.context || "").toLowerCase().includes(filters.context.toLowerCase())
    );
    //
    return (
        <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
            <Container>
                <Title>
                    🧠 Topic Memory — <span className="text-blue-600">{username || "anonymous"}</span>
                    <Badge type="default">Student</Badge>
                </Title>
                <p className={`mb-4 text-center ${darkMode ? "text-gray-300" : "text-gray-600"}`}>Your simulation of your memory</p>
                {weakness.grammar && (
                    <div className="mb-6 flex flex-col items-center gap-2">
                        <ProgressRing percentage={weakness.percent} />
                        <p className="text-sm">Weakest topic: <strong>{weakness.grammar}</strong></p>
                    </div>
                )}

                {topics.length === 0 ? (
                    <Alert type="info">No topic memory saved yet.</Alert>
                ) : (
                    <Card className="overflow-x-auto">
                        <table className={`min-w-full border rounded-lg overflow-hidden ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
                            <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
                                <tr>
                                    <th className="px-4 py-2 text-left">Grammar</th>
                                    <th className="px-4 py-2 text-left">Topic</th>
                                    <th className="px-4 py-2 text-left">Skill</th>
                                    <th className="px-4 py-2 text-left">Context</th>
                                    <th className="px-4 py-2 text-left">Ease</th>
                                    <th className="px-4 py-2 text-left">Interval</th>
                                    <th className="px-4 py-2 text-left">Next</th>
                                    <th className="px-4 py-2 text-left">Reps</th>
                                </tr>
                                <tr>
                                    <th className="px-2 py-1">
                                        <Input
                                            value={filters.grammar}
                                            onChange={(e) =>
                                                setFilters({ ...filters, grammar: e.target.value })
                                            }
                                            placeholder="filter"
                                            className="text-xs"
                                        />
                                    </th>
                                    <th className="px-2 py-1">
                                        <Input
                                            value={filters.topic}
                                            onChange={(e) =>
                                                setFilters({ ...filters, topic: e.target.value })
                                            }
                                            placeholder="filter"
                                            className="text-xs"
                                        />
                                    </th>
                                    <th className="px-2 py-1">
                                        <Input
                                            value={filters.skill}
                                            onChange={(e) =>
                                                setFilters({ ...filters, skill: e.target.value })
                                            }
                                            placeholder="filter"
                                            className="text-xs"
                                        />
                                    </th>
                                    <th className="px-2 py-1" colSpan="5">
                                        <Input
                                            value={filters.context}
                                            onChange={(e) =>
                                                setFilters({ ...filters, context: e.target.value })
                                            }
                                            placeholder="filter context"
                                            className="text-xs"
                                        />
                                    </th>
                                </tr>
                            </thead>
                            <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
                                {filteredTopics.map((t) => (
                                    <tr key={t.id} className={darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"}>
                                        <td className="px-4 py-2 font-medium">{t.grammar || "-"}</td>
                                        <td className="px-4 py-2">{t.topic || "-"}</td>
                                        <td className={`px-4 py-2 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>{t.skill_type}</td>
                                        <td className="px-4 py-2 whitespace-nowrap max-w-xs overflow-hidden text-ellipsis">{t.context}</td>
                                        <td className="px-4 py-2">{Number(t.ease_factor).toFixed(2)}</td>
                                        <td className="px-4 py-2">{t.intervall}</td>
                                        <td className="px-4 py-2">{t.next_repeat ? new Date(t.next_repeat).toLocaleDateString() : ""}</td>
                                        <td className="px-4 py-2">{t.repetitions}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </Card>
                )}
                <div className="mt-6 flex justify-center gap-4">
                    <Button variant="secondary" size="md" onClick={() => setFilters({ grammar: "", topic: "", skill: "", context: "" })}>
                        Reset Filters
                    </Button>
                    <Button variant="danger" size="md" onClick={() => setShowClear(true)}>
                        🗑️ Clear Memory
                    </Button>
                    <Button size="md" variant="ghost" type="button" onClick={() => navigate("/profile")}>🔙 Back to Profile</Button>
                </div>
            </Container>
            <Footer />
            {showClear && (
                <Modal onClose={() => setShowClear(false)}>
                    <h2 className="text-lg font-bold mb-2">Delete Topic Memory</h2>
                    <p className="mb-4">Are you sure you want to delete all saved topic memory?</p>
                    {error && <Alert type="error" className="mb-2">{error}</Alert>}
                    <div className="flex justify-end gap-2">
                        <Button variant="danger" onClick={handleClear}>Delete</Button>
                        <Button variant="secondary" onClick={() => setShowClear(false)}>
                            Cancel
                        </Button>
                    </div>
                </Modal>
            )}
        </div>
    );
}

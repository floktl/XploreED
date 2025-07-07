import React, { useEffect, useState } from "react";
import { getTopicMemory } from "../api";
import { Container, Title } from "./UI/UI";
import useAppStore from "../store/useAppStore";
import { useNavigate } from "react-router-dom";
import Footer from "./UI/Footer";

interface TopicEntry {
    id: number;
    grammar: string;
    quality: number;
}

interface GrammarAgg {
    grammar: string;
    avgQuality: number;
}

const NODE_SIZE = 80;
const GAP = 40;
const COLS = 5;

export default function GrammarMap() {
    const [nodes, setNodes] = useState<GrammarAgg[]>([]);
    const navigate = useNavigate();
    const darkMode = useAppStore((s) => s.darkMode);
    const username = useAppStore((s) => s.username);
    const isAdmin = useAppStore((s) => s.isAdmin);
    const isLoading = useAppStore((s) => s.isLoading);
    const setUsername = useAppStore((s) => s.setUsername);

    useEffect(() => {
        const stored = localStorage.getItem("username");
        if (!username && stored) setUsername(stored);
        if (!isLoading && (!username || isAdmin)) navigate(isAdmin ? "/admin-panel" : "/");
    }, [username, isAdmin, setUsername, navigate, isLoading]);

    useEffect(() => {
        getTopicMemory()
            .then((data: TopicEntry[]) => {
                const map: Record<string, { sum: number; count: number }> = {};
                data.forEach((t) => {
                    const key = t.grammar || "unknown";
                    if (!map[key]) map[key] = { sum: 0, count: 0 };
                    map[key].sum += t.quality || 0;
                    map[key].count += 1;
                });
                const aggs: GrammarAgg[] = Object.entries(map).map(([grammar, info]) => ({
                    grammar,
                    avgQuality: info.sum / info.count,
                }));
                setNodes(aggs);
            })
            .catch((err) => console.error("Failed to load topic memory", err));
    }, []);

    const width = COLS * (NODE_SIZE + GAP) + GAP;
    const rows = Math.ceil(nodes.length / COLS);
    const height = rows * (NODE_SIZE + GAP) + GAP;

    return (
        <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
            <Container>
                <Title>Grammar Map</Title>
                <div className="overflow-auto border rounded" style={{ height: "70vh" }}>
                    <svg width={width} height={height} className="bg-gray-100 dark:bg-gray-800">
                        {nodes.map((n, idx) => {
                            const col = idx % COLS;
                            const row = Math.floor(idx / COLS);
                            const x = GAP + col * (NODE_SIZE + GAP);
                            const y = GAP + row * (NODE_SIZE + GAP);
                            const opacity = Math.min(1, Math.max(0.2, n.avgQuality / 5));
                            const nextIdx = idx + 1;
                            const nextCol = nextIdx % COLS;
                            const nextRow = Math.floor(nextIdx / COLS);
                            const nextX = GAP + nextCol * (NODE_SIZE + GAP) + NODE_SIZE / 2;
                            const nextY = GAP + nextRow * (NODE_SIZE + GAP) + NODE_SIZE / 2;
                            return (
                                <g key={n.grammar}>
                                    {idx < nodes.length - 1 && (
                                        <line
                                            x1={x + NODE_SIZE / 2}
                                            y1={y + NODE_SIZE / 2}
                                            x2={nextX}
                                            y2={nextY}
                                            stroke="#60a5fa"
                                            strokeWidth={2}
                                        />
                                    )}
                                    <rect
                                        x={x}
                                        y={y}
                                        width={NODE_SIZE}
                                        height={NODE_SIZE}
                                        rx={10}
                                        fill={`rgba(59,130,246,${opacity})`}
                                        stroke="#1d4ed8"
                                    />
                                    <text
                                        x={x + NODE_SIZE / 2}
                                        y={y + NODE_SIZE / 2}
                                        textAnchor="middle"
                                        dominantBaseline="central"
                                        fontSize="12"
                                        fill={darkMode ? "white" : "#1e3a8a"}
                                    >
                                        {n.grammar}
                                    </text>
                                </g>
                            );
                        })}
                    </svg>
                </div>
            </Container>
            <Footer />
        </div>
    );
}


import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "../../components/common/UI/UI";
import Footer from "../../components/common/UI/Footer";
import useAppStore from "../../store/useAppStore";
import { getTopicMemory } from "../../services/api";
import { PageLayout } from "../../components/layout";
import {
	GrammarMapHeader,
	GrammarMapVisualization
} from "../../components/features/lessons";

export default function GrammarMapView() {
	const [nodes, setNodes] = useState([]);
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
			.then((data) => {
				const map = {};
				data.forEach((t) => {
					const key = t.grammar || "unknown";
					if (!map[key]) map[key] = { sum: 0, count: 0 };
					map[key].sum += t.quality || 0;
					map[key].count += 1;
				});
				const aggs = Object.entries(map).map(([grammar, info]) => ({
					grammar,
					avgQuality: info.sum / info.count,
				}));
				setNodes(aggs);
			})
			.catch((err) => console.error("Failed to load topic memory", err));
	}, []);

	return (
		<PageLayout variant="relative">
			<Container>
				<GrammarMapHeader />
				<GrammarMapVisualization nodes={nodes} darkMode={darkMode} />
			</Container>
			<Footer />
		</PageLayout>
	);
}

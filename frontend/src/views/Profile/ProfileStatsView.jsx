import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Container } from "../components/UI/UI";
import Alert from "../components/UI/Alert";
import Button from "../components/UI/Button";
import useAppStore from "../store/useAppStore";
import { fetchProfileStats } from "../api";
import {
	ProfileStatsHeader,
	ProfileStatsTable,
	ProfileStatsFooter
} from "../components/ProfileStats";

export default function ProfileStatsView() {
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
						Back to Admin Panel
					</Button>
				}
			>
				<ProfileStatsHeader username={username} />

				{error && <Alert type="error">{error}</Alert>}

				{!error && results.length === 0 ? (
					<Alert type="info">No data found.</Alert>
				) : (
					<ProfileStatsTable results={results} />
				)}
			</Container>
			<ProfileStatsFooter onNavigate={navigate} />
		</div>
	);
}

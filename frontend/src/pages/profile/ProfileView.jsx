import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "../../components/common/UI/UI";
import Alert from "../../components/common/UI/Alert";
import useAppStore from "../../store/useAppStore";
import { getMe, getRole, fetchProfileResults } from "../../services/api";
import { PageLayout } from "../../components/layout";
import {
	ProfileHeader,
	ProfileActions,
	ProfileControls
} from "../../components/features/profile";

export default function ProfileView() {
	const [results, setResults] = useState([]);
	const [error, setError] = useState("");

	const username = useAppStore((state) => state.username);
	const setUsername = useAppStore((state) => state.setUsername);
	const isAdmin = useAppStore((state) => state.isAdmin);
	const setIsAdmin = useAppStore((state) => state.setIsAdmin);
	const navigate = useNavigate();
	const darkMode = useAppStore((state) => state.darkMode);
	const toggleDarkMode = useAppStore((state) => state.toggleDarkMode);
	const setCurrentPageContent = useAppStore((s) => s.setCurrentPageContent);
	const clearCurrentPageContent = useAppStore((s) => s.clearCurrentPageContent);

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

	useEffect(() => {
		setCurrentPageContent({
			type: "profile",
			username,
			results
		});
		return () => clearCurrentPageContent();
	}, [username, results, setCurrentPageContent, clearCurrentPageContent]);

	return (
		<PageLayout variant="relative">
			<Container>
				<ProfileHeader username={username} darkMode={darkMode} />
				<ProfileActions onNavigate={navigate} />
				{error && <Alert type="error">{error}</Alert>}
				<ProfileControls
					onNavigate={navigate}
					onToggleDarkMode={toggleDarkMode}
					darkMode={darkMode}
				/>
			</Container>
		</PageLayout>
	);
}

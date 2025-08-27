import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "../components/UI/UI";
import Card from "../components/UI/Card";
import Alert from "../components/UI/Alert";
import useAppStore from "../store/useAppStore";
import { updatePassword, deactivateAccount } from "../api";
import {
	PasswordSection,
	LanguageSection,
	ThemeSection,
	DebugSection,
	SettingsFooter,
	DeleteAccountModal
} from "../components/Settings";

export default function SettingsView() {
	const [oldPw, setOldPw] = useState("");
	const [password, setPassword] = useState("");
	const [confirmPassword, setConfirmPassword] = useState("");
	const [error, setError] = useState("");
	const [success, setSuccess] = useState("");
	const [language, setLanguage] = useState("en");
	const [showDelete, setShowDelete] = useState(false);

	const navigate = useNavigate();
	const darkMode = useAppStore((state) => state.darkMode);
	const toggleDarkMode = useAppStore((state) => state.toggleDarkMode);
	const debugEnabled = useAppStore((state) => state.debugEnabled);
	const toggleDebugEnabled = useAppStore((state) => state.toggleDebugEnabled);

	const handlePasswordChange = async () => {
		if (!oldPw || !password || password !== confirmPassword) {
			setError("Missing fields or passwords do not match.");
			return;
		}

		try {
			await updatePassword(oldPw, password);
			setSuccess("Password updated successfully.");
			setError("");
			setOldPw("");
			setPassword("");
			setConfirmPassword("");
		} catch (err) {
			setError(err.message);
		}
	};

	const handleDeleteAll = async () => {
		try {
			await deactivateAccount(true);
			useAppStore.getState().resetStore();
			navigate("/");
		} catch (err) {
			setError(err.message);
		}
	};

	const handleAnonymize = async () => {
		try {
			await deactivateAccount(false);
			useAppStore.getState().resetStore();
			navigate("/");
		} catch (err) {
			setError(err.message);
		}
	};

	return (
		<div className="min-h-screen pb-32">
			<Container>
				<Card className="space-y-6">
					<PasswordSection
						oldPw={oldPw}
						setOldPw={setOldPw}
						password={password}
						setPassword={setPassword}
						confirmPassword={confirmPassword}
						setConfirmPassword={setConfirmPassword}
						onPasswordChange={handlePasswordChange}
					/>

					<LanguageSection
						language={language}
						setLanguage={setLanguage}
						darkMode={darkMode}
					/>

					<ThemeSection
						darkMode={darkMode}
						onToggleDarkMode={toggleDarkMode}
					/>

					<DebugSection
						debugEnabled={debugEnabled}
						onToggleDebugEnabled={toggleDebugEnabled}
					/>

					{error && <Alert type="warning">{error}</Alert>}
					{success && <Alert type="success">{success}</Alert>}
				</Card>
			</Container>

			<SettingsFooter
				onNavigate={navigate}
				onShowDelete={() => setShowDelete(true)}
			/>

			{showDelete && (
				<DeleteAccountModal
					onClose={() => setShowDelete(false)}
					onDeleteAll={handleDeleteAll}
					onAnonymize={handleAnonymize}
				/>
			)}
		</div>
	);
}

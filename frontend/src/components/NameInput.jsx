import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title, Input } from "./UI/UI";
import AskAiButton from "./AskAiButton";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";
import {
	PenSquare,
	Lock,
	Rocket,
	Eye,
	EyeOff,
	UserPlus,
	LogIn,
} from "lucide-react";
import { login, signup, getMe, getRole } from "../api";
import PlacementTest from "./PlacementTest";
import LevelGuess from "./LevelGuess";

export default function NameInput() {
	const [name, setName] = useState("");
	const [password, setPassword] = useState("");
	const [confirmPassword, setConfirmPassword] = useState("");
	const [showPassword, setShowPassword] = useState(false);
	const [error, setError] = useState("");
	const [isSignup, setIsSignup] = useState(false);
	const [showTest, setShowTest] = useState(false);
	const [showChoice, setShowChoice] = useState(false);
	const [showLevelSelect, setShowLevelSelect] = useState(false);
	const [enableDebug, setEnableDebug] = useState(false);
	const [autoSignupPrompt, setAutoSignupPrompt] = useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const navigate = useNavigate();

	const setUsername = useAppStore((state) => state.setUsername);
	const setDebugEnabled = useAppStore((state) => state.setDebugEnabled);
	const setIsAdmin = useAppStore((state) => state.setIsAdmin);
	const darkMode = useAppStore((state) => state.darkMode);

	const handleSubmit = async () => {
		const trimmed = name.trim();
		const pw = password.trim();
		const pwConfirm = confirmPassword.trim();

		if (!trimmed || !pw || (isSignup && !pwConfirm)) {
			setError("Please fill out all fields.");
			return;
		}

		if (isSignup && pw !== pwConfirm) {
			setError("Passwords do not match.");
			return;
		}

		try {
			setIsLoading(true);
			setError("");

			let res;
			if (isSignup) {
				res = await signup(trimmed, pw);
				if (res.error) {
					// Show friendly validation messages from backend
					if (
						res.error === "Validation error" &&
						Array.isArray(res.details) &&
						res.details.length > 0
					) {
						const messages = res.details
							.map((d) => d?.msg || d?.message)
							.filter(Boolean);
						const combined = messages.join("; ") ||
							"Please fix the highlighted fields.";
						setError(combined);
						return;
					}
					// Common constraints
					if (res.error.toLowerCase().includes("username")) {
						setError("Username must be 3-20 characters.");
						return;
					}
					if (res.error.toLowerCase().includes("password")) {
						setError("Password must be at least 6 characters.");
						return;
					}
					throw new Error(res.error);
				}
				res = await login(trimmed, pw);
				if (res.error) throw new Error(res.error);

				// Wait a bit for session to be established
				await new Promise((resolve) => setTimeout(resolve, 100));

				const me = await getMe();
				const role = await getRole();
				setUsername(me.username);
				setIsAdmin(role.is_admin);
				localStorage.setItem("username", me.username);
				setDebugEnabled(enableDebug);
				setShowChoice(true);
				return;
			} else {
				res = await login(trimmed, pw);
				if (res.error) {
					const errorCode = (res.error || "").toUpperCase();
					// If user does not exist -> switch to signup with info
					if (errorCode === "USER_NOT_FOUND" ||
						(res.message && res.message.toLowerCase().includes("no user"))) {
						setIsSignup(true);
						setAutoSignupPrompt(true);
						setError("");
						return;
					}
					// If wrong password -> show explicit message
					if (errorCode === "WRONG_PASSWORD" ||
						(res.message && res.message.toLowerCase().includes("wrong password"))) {
						setError("Wrong password");
						return;
					}
					// Fallback: show server message
					setError(res.message || res.error || "Could not log in. Try again.");
					return;
				}
			}

			// Wait a bit for session to be established
			await new Promise((resolve) => setTimeout(resolve, 100));

			const me = await getMe();
			const role = await getRole();

			setUsername(me.username);
			setIsAdmin(role.is_admin);
			localStorage.setItem("username", me.username);
			navigate("/menu");
		} catch (err) {
			console.error("[CLIENT] Auth failed:", err);
			setError(err.message || "Could not log in. Try again.");
		} finally {
			setIsLoading(false);
		}
	};

	const handleAdminRedirect = () => {
		navigate("/admin");
	};

	const handleDevFastLogin = async () => {
		try {
			setError("");
			setIsLoading(true);

			// Auto-login as test user
			const res = await login("tester1234", "thisisatest");
			if (res.error) throw new Error(res.error);

			// Wait a bit for session to be established
			await new Promise((resolve) => setTimeout(resolve, 100));

			const me = await getMe();
			const role = await getRole();
			setUsername(me.username);
			setIsAdmin(role.is_admin);
			localStorage.setItem("username", me.username);
			setDebugEnabled(enableDebug);

			// Skip level selection for test user and go directly to menu
			navigate("/menu");

			console.log("✅ Dev fast login successful:", { username: me.username, isAdmin: role.is_admin });
		} catch (err) {
			console.error("❌ Dev fast login failed:", err);
			setError("Dev fast login failed. Make sure backend is running with auto-login enabled.");
		} finally {
			setIsLoading(false);
		}
	};

	const getPasswordStrength = (pw) => {
		if (!pw) return "";
		if (pw.length < 6) return "Weak";
		if (pw.match(/[A-Z]/) && pw.match(/[0-9]/) && pw.length >= 8)
			return "Strong";
		return "Moderate";
	};

	if (showTest) {
		return <PlacementTest onComplete={() => navigate("/menu")} />;
	}

	if (showLevelSelect) {
		return <LevelGuess />;
	}

	if (showChoice) {
		return (
			<div
				className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}
			>
				<Container showHeader={true} minimalHeader={true}>
					<Title>Set Your Level</Title>
					<Card className="space-y-4 p-4 text-center">
						<p>
							Would you like to take a placement test or choose a level
							manually?
						</p>
						<div className="flex flex-col gap-4">
							<Button variant="primary" onClick={() => setShowTest(true)}>
								Take Placement Test
							</Button>
							<Button
								variant="secondary"
								onClick={() => setShowLevelSelect(true)}
							>
								Choose Level
							</Button>
						</div>
					</Card>
				</Container>
				<Footer />
			</div>
		);
	}

	return (
		<div
			className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}
		>
			<Container showHeader={true} minimalHeader={true}>
				<Title>{isSignup ? "Create an Account" : "Welcome"}</Title>
				<p
					className={`text-center mb-6 ${darkMode ? "text-gray-300" : "text-gray-600"}`}
				>
					{isSignup
						? "Choose your username and password."
						: "Please enter your name and password to begin:"}
				</p>

				<Card>
					<form
						className="space-y-4"
						onSubmit={(e) => {
							e.preventDefault();
							handleSubmit();
						}}
					>
						<div className="relative">
							<Input
								type="text"
								value={name}
								onChange={(e) => setName(e.target.value)}
								placeholder="Enter your name"
								autoFocus
								className="pl-10"
							/>
							<span className="absolute left-3 top-2.5 text-gray-400">
								<PenSquare className="w-5 h-5" />
							</span>
						</div>

						<div className="relative">
							<Input
								type={showPassword ? "text" : "password"}
								value={password}
								onChange={(e) => setPassword(e.target.value)}
								placeholder="Enter your password"
								className="pl-10"
							/>
							<span className="absolute left-3 top-2.5 text-gray-400">
								<Lock className="w-5 h-5" />
							</span>
							<span
								className="absolute right-3 top-2.5 text-gray-400 cursor-pointer select-none"
								onClick={() => setShowPassword(!showPassword)}
								title={showPassword ? "Hide password" : "Show password"}
							>
								{showPassword ? (
									<EyeOff className="w-5 h-5" />
								) : (
									<Eye className="w-5 h-5" />
								)}
							</span>
							{isSignup && password && (
								<p className="text-sm mt-1 text-gray-500 italic">
									Strength:{" "}
									<span
										className={
											getPasswordStrength(password) === "Strong"
												? "text-green-600"
												: getPasswordStrength(password) === "Moderate"
													? "text-yellow-600"
													: getPasswordStrength(password) === "Weak"
														? "text-red-600"
														: ""
										}
									>
										{getPasswordStrength(password)}
									</span>
								</p>
							)}
						</div>

						{isSignup && (
							<div className="relative">
								<Input
									type={showPassword ? "text" : "password"}
									value={confirmPassword}
									onChange={(e) => setConfirmPassword(e.target.value)}
									placeholder="Repeat your password"
									className="pl-10"
								/>
								<span className="absolute left-3 top-2.5 text-gray-400">
									<Lock className="w-5 h-5" />
								</span>
							</div>
						)}
						{isSignup && (
							<div className="flex items-center gap-2">
								<input
									type="checkbox"
									checked={enableDebug}
									onChange={(e) => setEnableDebug(e.target.checked)}
									id="debug-checkbox"
								/>
								<label htmlFor="debug-checkbox" className="text-sm">
									Enable debug features
								</label>
							</div>
						)}

						{error && <Alert type="warning">{error}</Alert>}
						{autoSignupPrompt && (
							<Alert type="info">
								No account found for this username. You can create a new account
								below!
							</Alert>
						)}

						<div className="flex flex-col sm:flex-row sm:space-x-4 space-y-2 sm:space-y-0">
							<Button
								variant="primary"
								type="submit"
								size="sm"
								disabled={isLoading}
								className="w-full sm:w-auto gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
							>
								{isLoading ? (
									<>
										<div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
										{isSignup ? "Signing Up..." : "Logging In..."}
									</>
								) : isSignup ? (
									<>
										<UserPlus className="w-4 h-4" /> Sign Up
									</>
								) : (
									<>
										<LogIn className="w-4 h-4" /> Log In
									</>
								)}
							</Button>
							<Button
								variant="secondary"
								type="button"
								onClick={handleAdminRedirect}
								disabled={isLoading}
								className="w-full sm:w-auto gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
							>
								<Lock className="w-4 h-4" />
								Admin Login
							</Button>
						</div>

						{/* Development Fast Login Button */}
						{import.meta.env.DEV && (
							<div className="border-t pt-4 mt-4">
								<div className="bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
									<div className="flex items-center justify-between mb-2">
										<span className="text-xs font-semibold text-yellow-800 dark:text-yellow-200 uppercase tracking-wide">
											🛠️ Development Mode
										</span>
										<span className="text-xs bg-yellow-200 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200 px-2 py-1 rounded-full">
											DEV
										</span>
									</div>
									<Button
										variant="ghost"
										type="button"
										onClick={handleDevFastLogin}
										disabled={isLoading}
										className="w-full gap-2 bg-yellow-100 border-yellow-300 text-yellow-900 hover:bg-yellow-200 dark:bg-yellow-800/30 dark:border-yellow-700 dark:text-yellow-100 dark:hover:bg-yellow-800/50 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
									>
										<Rocket className="w-4 h-4" />
										{isLoading ? "🔄 Logging in..." : "🚀 Dev Fast Login (tester1234)"}
									</Button>
									<p className="text-xs text-center mt-2 text-yellow-700 dark:text-yellow-300">
										Auto login as test user with level 3
									</p>
								</div>
							</div>
						)}

						<div className="text-center pt-2 text-sm">
							{isSignup ? (
								<>
									Already have an account?{" "}
									<button
										type="button"
										onClick={() => {
											setIsSignup(false);
											setAutoSignupPrompt(false);
										}}
										className="text-blue-500 underline"
									>
										Log in
									</button>
								</>
							) : (
								<>
									Don't have an account?{" "}
									<button
										type="button"
										onClick={() => setIsSignup(true)}
										className="text-blue-500 underline"
									>
										Sign up
									</button>
								</>
							)}
						</div>
					</form>
				</Card>
			</Container>
			<Footer>
				<Button
					variant="link"
					type="button"
					onClick={() => navigate("/terms-of-service")}
					className="w-full gap-2"
				>
					Terms of Service
				</Button>
			</Footer>
		</div>
	);
}

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "../../../common/UI/Button";
import { Container, Title } from "../../../common/UI/UI";
import AskAiButton from "../../ai/AskAiButton/AskAiButton";
import Card from "../../../common/UI/Card";
import Alert from "../../../common/UI/Alert";
import Footer from "../../../common/UI/Footer";
import useAppStore from "../../../../store/useAppStore";
import {
    PenSquare,
    Lock,
    Rocket,
} from "lucide-react";
import { login, signup, getMe, getRole } from "../../../../services/api";
import PlacementTestView from "../../../../pages/game/PlacementTestView";
import LevelGuessView from "../../../../pages/game/LevelGuessView";

// Import modular components
import LoginForm from "./Forms/LoginForm";
import SignupForm from "./Forms/SignupForm";
import PasswordStrength from "./Validation/PasswordStrength";

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
                    if (errorCode === "USER_NOT_FOUND" ||
                        (res.message && res.message.toLowerCase().includes("no user"))) {
                        setIsSignup(true);
                        setAutoSignupPrompt(true);
                        setError("");
                        return;
                    }
                    if (errorCode === "WRONG_PASSWORD" ||
                        (res.message && res.message.toLowerCase().includes("wrong password"))) {
                        setError("Wrong password");
                        return;
                    }
                    setError(res.message || res.error || "Could not log in. Try again.");
                    return;
                }
            }

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

            const res = await login("tester1234", "thisisatest");
            if (res.error) throw new Error(res.error);

            await new Promise((resolve) => setTimeout(resolve, 100));

            const me = await getMe();
            const role = await getRole();
            setUsername(me.username);
            setIsAdmin(role.is_admin);
            localStorage.setItem("username", me.username);
            setDebugEnabled(enableDebug);

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
        return <PlacementTestView onComplete={() => navigate("/menu")} />;
    }

    if (showLevelSelect) {
        return <LevelGuessView />;
    }

    if (showChoice) {
        return (
            <div className={`min-h-screen flex items-center justify-center ${darkMode ? "bg-gray-900 text-white" : "bg-gray-50 text-gray-800"}`}>
                <Container>
                    <Card className="max-w-md mx-auto">
                        <div className="text-center mb-6">
                            <h2 className="text-2xl font-bold mb-2">Welcome to XplorED!</h2>
                            <p className="text-gray-600 dark:text-gray-400">
                                What would you like to do first?
                            </p>
                        </div>

                        <div className="space-y-4">
                            <Button
                                onClick={() => setShowTest(true)}
                                className="w-full gap-2"
                                variant="primary"
                            >
                                <PenSquare className="w-4 h-4" />
                                Take Placement Test
                            </Button>

                            <Button
                                onClick={() => setShowLevelSelect(true)}
                                className="w-full gap-2"
                                variant="secondary"
                            >
                                <Lock className="w-4 h-4" />
                                Choose My Level
                            </Button>

                            <Button
                                onClick={() => navigate("/menu")}
                                className="w-full gap-2"
                                variant="success"
                            >
                                <Rocket className="w-4 h-4" />
                                Start Learning
                            </Button>
                        </div>
                    </Card>
                </Container>
            </div>
        );
    }

    return (
        <div className={`min-h-screen flex items-center justify-center ${darkMode ? "bg-gray-900 text-white" : "bg-gray-50 text-gray-800"}`}>
            <Container>
                <Card className="max-w-md mx-auto">
                    <div className="text-center mb-6">
                        <Title>Welcome to XplorED</Title>
                        <p className="text-gray-600 dark:text-gray-400 mt-2">
                            {isSignup ? "Create your account" : "Sign in to continue"}
                        </p>
                    </div>

                    {error && (
                        <Alert variant="error" className="mb-4">
                            {error}
                        </Alert>
                    )}

                    {autoSignupPrompt && (
                        <Alert variant="info" className="mb-4">
                            User not found. Would you like to create a new account?
                        </Alert>
                    )}

                    {isSignup ? (
                        <SignupForm
                            name={name}
                            setName={setName}
                            password={password}
                            setPassword={setPassword}
                            confirmPassword={confirmPassword}
                            setConfirmPassword={setConfirmPassword}
                            showPassword={showPassword}
                            setShowPassword={setShowPassword}
                            isLoading={isLoading}
                            onSubmit={handleSubmit}
                            onSwitchToLogin={() => {
                                setIsSignup(false);
                                setAutoSignupPrompt(false);
                                setError("");
                            }}
                            passwordStrength={getPasswordStrength(password)}
                        />
                    ) : (
                        <LoginForm
                            name={name}
                            setName={setName}
                            password={password}
                            setPassword={setPassword}
                            showPassword={showPassword}
                            setShowPassword={setShowPassword}
                            isLoading={isLoading}
                            onSubmit={handleSubmit}
                            onSwitchToSignup={() => {
                                setIsSignup(true);
                                setAutoSignupPrompt(false);
                                setError("");
                            }}
                        />
                    )}

                    <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                        <div className="space-y-3">
                            <Button
                                onClick={handleDevFastLogin}
                                disabled={isLoading}
                                variant="ghost"
                                size="sm"
                                className="w-full text-xs"
                            >
                                🚀 Dev Fast Login
                            </Button>

                            <div className="flex items-center justify-between text-xs text-gray-500">
                                <label className="flex items-center">
                                    <input
                                        type="checkbox"
                                        checked={enableDebug}
                                        onChange={(e) => setEnableDebug(e.target.checked)}
                                        className="mr-2"
                                    />
                                    Enable Debug Mode
                                </label>
                            </div>
                        </div>
                    </div>
                </Card>
            </Container>
            <Footer />
            <AskAiButton />
        </div>
    );
}

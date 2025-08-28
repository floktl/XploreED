import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "../../components/common/UI/Button";
import { Container, Title, Input } from "../../components/common/UI/UI";
import Card from "../../components/common/UI/Card";
import { Lock, ArrowLeft } from "lucide-react";
import Alert from "../../components/common/UI/Alert";
import Footer from "../../components/common/UI/Footer";
import useAppStore from "../../store/useAppStore";
import { verifyAdminPassword } from "../../services/api";
import { PageLayout } from "../../components/layout";

export default function AdminLogin() {
	const [password, setPassword] = useState("");
	const [error, setError] = useState("");
	const navigate = useNavigate();

	const darkMode = useAppStore((state) => state.darkMode);
	const setIsAdmin = useAppStore((state) => state.setIsAdmin);

	const handleLogin = async () => {
		try {
			const success = await verifyAdminPassword(password); // ✅ 2. Use API helper

			if (success) {
				setIsAdmin(true);
				navigate("/admin-panel");
			} else {
				setError("Login failed. Wrong password?");
			}
		} catch (err) {
			console.error("[CLIENT] Login failed:", err);
			setError("Server error. Please try again.");
		}
	};


	return (
		<PageLayout variant="relative">
			<Container
				bottom={
					<Button onClick={() => navigate("/")} variant="link" type="submit" className="w-full gap-2">
						<ArrowLeft className="w-4 h-4" />
						Back to Student Login
					</Button>
				}
			>
				<Title>🔐 Admin Login</Title>

				<Card>
					<div className="space-y-4">
						<Input
							type="password"
							placeholder="Enter Admin Password"
							value={password}
							onChange={(e) => setPassword(e.target.value)}
						/>

						{error && <Alert type="error">{error}</Alert>}

						<Button onClick={handleLogin} variant="primary" type="submit" className="w-full gap-2">
							<Lock className="w-4 h-4" />
							Login
						</Button>

					</div>
				</Card>
			</Container>

			<Footer>
				<Button onClick={() => navigate("/")} variant="link" type="submit" className="w-full gap-2">
					<ArrowLeft className="w-4 h-4" />
					Back to Student Login
				</Button>
			</Footer>
		</PageLayout>
	);
}

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { XCircle, ArrowLeft } from "lucide-react";
import Button from "./UI/Button";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import useAppStore from "../store/useAppStore";
import Footer from "./UI/Footer";
import Modal from "./UI/Modal";
import { updatePassword, deactivateAccount } from "../api";
import clsx from "clsx";

export default function Settings() {
    const [oldPw, setOldPw] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [language, setLanguage] = useState("en");
    const [showDelete, setShowDelete] = useState(false);
    const debugEnabled = useAppStore((state) => state.debugEnabled);
    const toggleDebugEnabled = useAppStore((state) => state.toggleDebugEnabled);

    const navigate = useNavigate();
    const darkMode = useAppStore((state) => state.darkMode);
    const toggleDarkMode = useAppStore((state) => state.toggleDarkMode);

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
                    {/* Change Password */}
                    <div className="space-y-2">
                        <label className="block font-semibold">Change Password</label>
                        <Input
                            type="password"
                            placeholder="Current Password"
                            value={oldPw}
                            onChange={(e) => setOldPw(e.target.value)}
                        />
                        <Input
                            type="password"
                            placeholder="New Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                        <Input
                            type="password"
                            placeholder="Confirm Password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                        />
                        <Button variant="primary" onClick={handlePasswordChange}>
                            🔐 Update Password
                        </Button>
                    </div>

                    {/* Language Toggle */}
                    <div className="space-y-2">
                        <label className="block font-semibold">Language</label>
                        <select
                            className={clsx(
                                "border rounded px-3 py-2",
                                darkMode
                                    ? "bg-gray-800 text-white border-gray-700"
                                    : "bg-white text-gray-900 border-gray-200"
                            )}
                            value={language}
                            onChange={(e) => setLanguage(e.target.value)}
                        >
                            <option value="en">English</option>
                            <option value="de">Deutsch</option>
                        </select>
                    </div>

                    {/* Theme Toggle */}
                    <div className="space-y-2">
                        <label className="block font-semibold">Theme</label>
                        <Button variant="secondary" onClick={toggleDarkMode}>
                            {darkMode ? "Switch to Light" : "Switch to Dark"}
                        </Button>
                    </div>
                    {/* Debug Toggle */}
                    <div className="space-y-2">
                        <label className="block font-semibold">Debug Features</label>
                        <Button variant="secondary" onClick={toggleDebugEnabled}>
                            {debugEnabled ? "Disable Debug" : "Enable Debug"}
                        </Button>
                    </div>

                    {/* Feedback */}
                    {error && <Alert type="warning">{error}</Alert>}
                    {success && <Alert type="success">{success}</Alert>}
                </Card>
            </Container>

<Footer>
    <Button
        size="md"
        variant="ghost"
        type="button"
        onClick={() => navigate("/profile")}
        className="gap-2"
    >
        <ArrowLeft className="w-4 h-4" />
        Back
    </Button>
    <Button
        variant="danger"
        onClick={() => setShowDelete(true)}
        className="gap-2"
    >
        <XCircle className="w-4 h-4" />
        Delete Account
    </Button>
</Footer>


            {/* Delete Modal */}
            {showDelete && (
                <Modal onClose={() => setShowDelete(false)}>
                    <h2 className="text-lg font-bold mb-2">Delete Account</h2>
                    <p className="mb-4">Would you like to delete all data or allow it to be anonymized for research?</p>
                    <div className="flex justify-end gap-2">
                        <Button variant="danger" onClick={handleDeleteAll}>Delete All</Button>
                        <Button variant="secondary" onClick={handleAnonymize}>Anonymize</Button>
                    </div>
                </Modal>
            )}
        </div>
    );
}

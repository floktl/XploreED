import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import useAppStore from "../store/useAppStore";
import Footer from "./UI/Footer";
import { updatePassword, uploadAvatar, deactivateAccount } from "../api";

export default function Settings() {
  const [oldPw, setOldPw] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [language, setLanguage] = useState("en");
  const [image, setImage] = useState(null);
  const navigate = useNavigate();

  const handlePasswordChange = async () => {
    if (!oldPw || !password || password !== confirmPassword) {
      setError("❌ Missing fields or passwords do not match.");
      return;
    }
  
    try {
      await updatePassword(oldPw, password);
      setSuccess("✅ Password updated successfully.");
      setError("");
      setOldPw("");
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError("❌ " + err.message);
    }
  };
  
  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
  
    try {
      await uploadAvatar(file);
      setSuccess("✅ Avatar uploaded successfully.");
      setError("");
    } catch (err) {
      setError("❌ " + err.message);
    }
  };
  
  const handleDeactivate = async () => {
    try {
      await deactivateAccount();
      useAppStore.getState().resetStore();
      navigate("/");
    } catch (err) {
      setError("❌ " + err.message);
    }
  };
  

  return (
    <div className="min-h-screen pb-24">
      <Container>
        <Title>⚙️ Settings</Title>

        <Card>
          <div className="space-y-6">
            {/* Change Password */}
            <div>
              <label className="block font-semibold mb-1">Change Password</label>
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

            {/* Upload Avatar */}
            <div>
              <label className="block font-semibold mb-1">Upload Avatar</label>
              <Input type="file" onChange={handleImageUpload} />
            </div>

            {/* Language Toggle */}
            <div>
              <label className="block font-semibold mb-1">Language</label>
              <select
                className="border p-2 rounded"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="en">English</option>
                <option value="de">Deutsch</option>
              </select>
            </div>

            {/* Deactivate Account */}
            <div>
              <Button variant="danger" onClick={handleDeactivate}>
                ❌ Deactivate Account
              </Button>
            </div>

            {/* Feedback */}
            {error && <Alert type="warning">{error}</Alert>}
            {success && <Alert type="success">{success}</Alert>}
          </div>
        </Card>
      </Container>
      <Footer />
    </div>
  );
}

import React from "react";
import { Input } from "../UI/UI";
import Button from "../UI/Button";

export default function PasswordSection({
  oldPw,
  setOldPw,
  password,
  setPassword,
  confirmPassword,
  setConfirmPassword,
  onPasswordChange
}) {
  return (
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
      <Button variant="primary" onClick={onPasswordChange}>
        🔐 Update Password
      </Button>
    </div>
  );
}

import React from "react";
import Button from "../../../../common/UI/Button";
import { Input } from "../../../../common/UI/UI";
import { UserPlus } from "lucide-react";

interface CreateUserFormProps {
    newUser: { username: string; password: string; skill_level?: number };
    setNewUser: (user: { username: string; password: string; skill_level?: number }) => void;
    repeatPassword: string;
    setRepeatPassword: (password: string) => void;
    onSubmit: () => void;
    onCancel: () => void;
    isLoading: boolean;
}

export default function CreateUserForm({
    newUser,
    setNewUser,
    repeatPassword,
    setRepeatPassword,
    onSubmit,
    onCancel,
    isLoading
}: CreateUserFormProps) {
    const passwordsMatch = newUser.password === repeatPassword;
    const isValid = newUser.username.trim() && newUser.password.trim() && passwordsMatch;

    return (
        <div className="space-y-4">
            <div>
                <label className="block text-sm font-medium mb-2">Username</label>
                <Input
                    type="text"
                    value={newUser.username}
                    onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                    placeholder="Enter username"
                    disabled={isLoading}
                />
            </div>

            <div>
                <label className="block text-sm font-medium mb-2">Password</label>
                <Input
                    type="password"
                    value={newUser.password}
                    onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                    placeholder="Enter password"
                    disabled={isLoading}
                />
            </div>

            <div>
                <label className="block text-sm font-medium mb-2">Confirm Password</label>
                <Input
                    type="password"
                    value={repeatPassword}
                    onChange={(e) => setRepeatPassword(e.target.value)}
                    placeholder="Confirm password"
                    disabled={isLoading}
                    className={!passwordsMatch && repeatPassword ? "border-red-500" : ""}
                />
                {!passwordsMatch && repeatPassword && (
                    <p className="text-red-500 text-sm mt-1">Passwords do not match</p>
                )}
            </div>

            <div>
                <label className="block text-sm font-medium mb-2">Skill Level (optional)</label>
                <Input
                    type="number"
                    value={newUser.skill_level || ""}
                    onChange={(e) => setNewUser({ ...newUser, skill_level: parseInt(e.target.value) || 0 })}
                    placeholder="Enter skill level"
                    disabled={isLoading}
                    min="0"
                    max="10"
                />
            </div>

            <div className="flex gap-3 pt-4">
                <Button
                    onClick={onSubmit}
                    disabled={!isValid || isLoading}
                    className="flex-1 gap-2"
                >
                    <UserPlus className="w-4 h-4" />
                    {isLoading ? "Creating..." : "Create User"}
                </Button>
                <Button
                    onClick={onCancel}
                    variant="secondary"
                    disabled={isLoading}
                >
                    Cancel
                </Button>
            </div>
        </div>
    );
}

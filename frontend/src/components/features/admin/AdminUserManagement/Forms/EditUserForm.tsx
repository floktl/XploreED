import React from "react";
import Button from "../../../../common/UI/Button";
import { Input } from "../../../../common/UI/UI";
import { Save, X } from "lucide-react";

interface User {
    username: string;
    created_at?: string;
    skill_level?: number;
    password?: string;
    original?: string;
}

interface EditUserFormProps {
    user: User;
    setUser: (user: User) => void;
    onSave: () => void;
    onCancel: () => void;
    isLoading: boolean;
}

export default function EditUserForm({
    user,
    setUser,
    onSave,
    onCancel,
    isLoading
}: EditUserFormProps) {
    const isValid = user.username.trim();

    return (
        <div className="space-y-4">
            <div>
                <label className="block text-sm font-medium mb-2">Username</label>
                <Input
                    type="text"
                    value={user.username}
                    onChange={(e) => setUser({ ...user, username: e.target.value })}
                    placeholder="Enter username"
                    disabled={isLoading}
                />
            </div>

            <div>
                <label className="block text-sm font-medium mb-2">Password (leave blank to keep current)</label>
                <Input
                    type="password"
                    value={user.password || ""}
                    onChange={(e) => setUser({ ...user, password: e.target.value })}
                    placeholder="Enter new password"
                    disabled={isLoading}
                />
            </div>

            <div>
                <label className="block text-sm font-medium mb-2">Skill Level</label>
                <Input
                    type="number"
                    value={user.skill_level || ""}
                    onChange={(e) => setUser({ ...user, skill_level: parseInt(e.target.value) || 0 })}
                    placeholder="Enter skill level"
                    disabled={isLoading}
                    min="0"
                    max="10"
                />
            </div>

            <div className="flex gap-3 pt-4">
                <Button
                    onClick={onSave}
                    disabled={!isValid || isLoading}
                    className="flex-1 gap-2"
                >
                    <Save className="w-4 h-4" />
                    {isLoading ? "Saving..." : "Save Changes"}
                </Button>
                <Button
                    onClick={onCancel}
                    variant="secondary"
                    disabled={isLoading}
                    className="gap-2"
                >
                    <X className="w-4 h-4" />
                    Cancel
                </Button>
            </div>
        </div>
    );
}

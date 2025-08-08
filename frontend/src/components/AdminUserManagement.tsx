import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import useRequireAdmin from "../hooks/useRequireAdmin";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Modal from "./UI/Modal";
import Alert from "./UI/Alert";

import useAppStore from "../store/useAppStore";
import { fetchUsers, updateUserAccount, deleteUserAccount } from "../api";
import { signup } from "../api";
import {
    Users,
    Plus,
    ArrowLeft,
    Edit,
    Trash2,
    Save,
    X,
    User,
    Target,
    Calendar,
    Shield,
    UserPlus,
    Settings
} from "lucide-react";

interface User {
    username: string;
    created_at?: string;
    skill_level?: number;
    password?: string;
    original?: string;
}

export default function AdminUserManagement() {
    useRequireAdmin();
    const [users, setUsers] = useState<User[]>([]);
    const [editUser, setEditUser] = useState<User | null>(null);
    const [error, setError] = useState("");
    const [userToDelete, setUserToDelete] = useState<string | null>(null);
    const [showCreate, setShowCreate] = useState(false);
    const [newUser, setNewUser] = useState<{username: string; password: string; skill_level?: number}>({username: "", password: "", skill_level: 0});
    const [repeatPassword, setRepeatPassword] = useState("");
    const darkMode = useAppStore((s) => s.darkMode);

    // Load users and auto-refresh while the page is open
    useEffect(() => {
        let isMounted = true;

        const load = async () => {
            try {
                const data = await fetchUsers();
                const list = Array.isArray(data)
                    ? data
                    : Array.isArray(data?.users)
                        ? data.users
                        : [];
                if (isMounted) {
                    setUsers(list);
                }
            } catch {
                if (isMounted) setError("Failed to load users");
            }
        };

        // Initial load
        load();

        // Poll every 5 seconds
        const intervalId = window.setInterval(load, 5000);

        return () => {
            isMounted = false;
            window.clearInterval(intervalId);
        };
    }, []);

    const handleSave = async () => {
        if (!editUser) return;
        try {
            await updateUserAccount(editUser.original || editUser.username, {
                username: editUser.username,
                password: editUser.password,
                skill_level: editUser.skill_level,
            });
            const data = await fetchUsers();
            const list = Array.isArray(data)
                ? data
                : Array.isArray(data?.users)
                    ? data.users
                    : [];
            setUsers(list);
            setEditUser(null);
        } catch {
            setError("Failed to update user");
        }
    };

    const requestDelete = (username: string) => {
        setUserToDelete(username);
    };

    const confirmDelete = async () => {
        if (!userToDelete) return;
        try {
            await deleteUserAccount(userToDelete);
            setUsers((u) => u.filter((x) => x.username !== userToDelete));
            setError("");
        } catch {
            setError("Failed to delete user");
        } finally {
            setUserToDelete(null);
        }
    };

    const passwordsMatch = newUser.password === repeatPassword;

    const handleCreate = async () => {
        if (!newUser.username.trim() || !newUser.password.trim()) {
            setError("Username and password required");
            return;
        }
        if (!passwordsMatch) {
            setError("Passwords do not match");
            return;
        }
        try {
            const res = await signup(newUser.username.trim(), newUser.password.trim());
            if (res.error) throw new Error(res.error);
            // Optionally set skill_level if API supports it (not shown in current API)
            const data = await fetchUsers();
            setUsers(Array.isArray(data) ? data : []);
            setShowCreate(false);
            setNewUser({username: "", password: "", skill_level: 0});
            setRepeatPassword("");
            setError("");
        } catch (err: any) {
            setError(err.message || "Failed to create user");
        }
    };

    // Defensive filtering: only show users with a valid, non-empty username
    const validUsers = users.filter(u => u.username && u.username.trim() !== "");
    const skippedCount = users.length - validUsers.length;

    return (
        <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
            <Container>
                                {/* Header Section */}
                <div className="mb-6">
                    <div className="flex items-center gap-3 mb-4">
                        <Shield className={`w-8 h-8 ${darkMode ? "text-blue-400" : "text-blue-600"}`} />
                        <Title className="mb-0">User Management</Title>
                    </div>
                    <Button
                        variant="success"
                        size="auto"
                        onClick={() => { setShowCreate(true); setError(""); }}
                        className="gap-2"
                    >
                        <UserPlus className="w-4 h-4" />
                        Add User
                    </Button>
                </div>



                {/* Alerts */}
                {error && <Alert type="danger">{error}</Alert>}
                {skippedCount > 0 && (
                    <Alert type="warning">
                        {skippedCount} user(s) skipped due to missing or invalid username.
                    </Alert>
                )}

                {/* Users Table */}
                <Card className="mb-8">
                    <div className="flex items-center gap-3 mb-4">
                        <Users className={`w-6 h-6 ${darkMode ? "text-blue-400" : "text-blue-600"}`} />
                        <h2 className="text-xl font-bold">All Users</h2>
                    </div>

                    <div className="overflow-x-auto">
                        <div className="hidden sm:block">
                            <table className={`min-w-full border rounded-lg ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
                                <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
                                    <tr>
                                        <th className="px-4 py-3 text-left font-semibold">User</th>
                                        <th className="px-4 py-3 text-left font-semibold">Skill Level</th>
                                        <th className="px-4 py-3 text-left font-semibold">Created</th>
                                        <th className="px-4 py-3 text-left font-semibold">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className={darkMode ? "bg-gray-800 divide-gray-700" : "bg-white divide-gray-200"}>
                                    {validUsers.length === 0 ? (
                                        <tr>
                                            <td colSpan={4} className="px-4 py-8 text-center text-gray-400 italic">
                                                <User className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                                No users found
                                            </td>
                                        </tr>
                                    ) : (
                                        validUsers.map((u) => (
                                            <tr key={u.username} className={`${darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"} transition-colors`}>
                                                <td className="px-4 py-3 font-semibold">{u.username}</td>
                                                <td className="px-4 py-3">
                                                    <div className="flex items-center gap-2">
                                                        <Target className="w-4 h-4 text-green-500" />
                                                        {u.skill_level ?? "—"}
                                                    </div>
                                                </td>
                                                <td className="px-4 py-3">
                                                    <div className="flex items-center gap-2">
                                                        <Calendar className="w-4 h-4 text-gray-400" />
                                                        {u.created_at ? new Date(u.created_at).toLocaleString() : "—"}
                                                    </div>
                                                </td>
                                                <td className="px-4 py-3">
                                                    <div className="flex gap-2">
                                                        <Button
                                                            size="auto"
                                                            variant="secondary"
                                                            onClick={() => setEditUser({ ...u, original: u.username })}
                                                            className="gap-2"
                                                        >
                                                            <Edit className="w-4 h-4" />
                                                            Edit
                                                        </Button>
                                                        <Button
                                                            size="auto"
                                                            variant="danger"
                                                            onClick={() => requestDelete(u.username)}
                                                            className="gap-2"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                            Delete
                                                        </Button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {/* Mobile layout */}
                        <div className="sm:hidden flex flex-col gap-4">
                            {validUsers.length === 0 ? (
                                <div className="text-center py-8 text-gray-400">
                                    <User className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                    <p>No users found</p>
                                </div>
                            ) : (
                                validUsers.map((u) => (
                                    <div key={u.username} className={`rounded-lg border p-4 ${darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-gray-200"}`}>
                                        <div className="flex items-center justify-between mb-3">
                                            <div className="flex items-center gap-2">
                                                <User className="w-5 h-5 text-blue-500" />
                                                <span className="font-semibold">{u.username}</span>
                                            </div>
                                        </div>
                                        <div className="space-y-2 mb-4">
                                            <div className="flex items-center gap-2">
                                                <Target className="w-4 h-4 text-green-500" />
                                                <span className="text-sm text-gray-600">Skill Level: {u.skill_level ?? "—"}</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Calendar className="w-4 h-4 text-gray-400" />
                                                <span className="text-sm text-gray-600">
                                                    Created: {u.created_at ? new Date(u.created_at).toLocaleString() : "—"}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex gap-2">
                                            <Button
                                                size="auto"
                                                variant="secondary"
                                                onClick={() => setEditUser({ ...u, original: u.username })}
                                                className="gap-2 flex-1"
                                            >
                                                <Edit className="w-4 h-4" />
                                                Edit
                                            </Button>
                                            <Button
                                                size="auto"
                                                variant="danger"
                                                onClick={() => requestDelete(u.username)}
                                                className="gap-2 flex-1"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                                Delete
                                            </Button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </Card>
            </Container>

            {/* Edit User Modal */}
            {editUser && (
                <Modal onClose={() => setEditUser(null)}>
                    <div className="flex items-center gap-3 mb-4">
                        <Settings className="w-6 h-6 text-blue-500" />
                        <h2 className="text-xl font-bold">Edit User: {editUser.original}</h2>
                    </div>

                    <Input
                        type="text"
                        value={editUser.username}
                        onChange={(e) => setEditUser({ ...editUser, username: e.target.value })}
                        className="mb-3"
                        placeholder="Username"
                    />
                    <Input
                        type="password"
                        placeholder="New Password (leave blank to keep current)"
                        onChange={(e) => setEditUser({ ...editUser, password: e.target.value })}
                        className="mb-3"
                    />
                    <Input
                        type="number"
                        value={editUser.skill_level ?? 0}
                        onChange={(e) => setEditUser({ ...editUser, skill_level: parseInt(e.target.value) })}
                        className="mb-4"
                        placeholder="Skill Level"
                    />
                    <div className="flex gap-2">
                        <Button variant="success" onClick={handleSave} className="gap-2">
                            <Save className="w-4 h-4" />
                            Save Changes
                        </Button>
                        <Button variant="secondary" onClick={() => setEditUser(null)} className="gap-2">
                            <X className="w-4 h-4" />
                            Cancel
                        </Button>
                    </div>
                </Modal>
            )}

            {/* Create User Modal */}
            {showCreate && (
                <Modal onClose={() => { setShowCreate(false); setRepeatPassword(""); }}>
                    <div className="flex items-center gap-3 mb-4">
                        <UserPlus className="w-6 h-6 text-blue-500" />
                        <h2 className="text-xl font-bold">Create New User</h2>
                    </div>

                    <Input
                        type="text"
                        value={newUser.username}
                        onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                        className="mb-3"
                        placeholder="Username"
                    />
                    <Input
                        type="password"
                        value={newUser.password}
                        onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                        className="mb-3"
                        placeholder="Password"
                    />
                    <Input
                        type="password"
                        value={repeatPassword}
                        onChange={(e) => setRepeatPassword(e.target.value)}
                        className="mb-3"
                        placeholder="Confirm Password"
                    />
                    {!passwordsMatch && repeatPassword && (
                        <Alert type="warning">Passwords do not match.</Alert>
                    )}
                    {error && <Alert type="danger">{error}</Alert>}
                    <div className="flex gap-2 mt-4">
                        <Button variant="success" onClick={handleCreate} disabled={!passwordsMatch} className="gap-2">
                            <UserPlus className="w-4 h-4" />
                            Create User
                        </Button>
                        <Button variant="secondary" onClick={() => setShowCreate(false)} className="gap-2">
                            <X className="w-4 h-4" />
                            Cancel
                        </Button>
                    </div>
                </Modal>
            )}

            {/* Confirm Delete Modal */}
            {userToDelete && (
                <Modal onClose={() => setUserToDelete(null)}>
                    <div className="mb-4">
                        <h2 className="text-xl font-bold">Delete User</h2>
                        <p className="mt-2">Are you sure you want to delete <strong>{userToDelete}</strong>? This action cannot be undone.</p>
                    </div>
                    <div className="flex gap-2 justify-end">
                        <Button variant="secondary" onClick={() => setUserToDelete(null)} className="gap-2">
                            <X className="w-4 h-4" />
                            Cancel
                        </Button>
                        <Button variant="danger" onClick={confirmDelete} className="gap-2">
                            <Trash2 className="w-4 h-4" />
                            Delete
                        </Button>
                    </div>
                </Modal>
            )}

                        <div className="mt-8 text-center pb-8">
                <Link
                    to="/admin-panel"
                    className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition-colors ${
                        darkMode
                            ? "bg-gray-700 hover:bg-gray-600 text-white"
                            : "bg-blue-50 hover:bg-blue-100 text-blue-700"
                    }`}
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back to Dashboard
                </Link>
            </div>
        </div>
    );
}


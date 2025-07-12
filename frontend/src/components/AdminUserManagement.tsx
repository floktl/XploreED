import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import useRequireAdmin from "../hooks/useRequireAdmin";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Modal from "./UI/Modal";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";
import { fetchUsers, updateUserAccount, deleteUserAccount } from "../api";
import { signup } from "../api";

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
    const [showCreate, setShowCreate] = useState(false);
    const [newUser, setNewUser] = useState<{username: string; password: string; skill_level?: number}>({username: "", password: "", skill_level: 0});
    const [repeatPassword, setRepeatPassword] = useState("");
    const darkMode = useAppStore((s) => s.darkMode);

    useEffect(() => {
        const load = async () => {
            try {
                const data = await fetchUsers();
                setUsers(Array.isArray(data) ? data : []);
            } catch {
                setError("Failed to load users");
            }
        };
        load();
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
            setUsers(Array.isArray(data) ? data : []);
            setEditUser(null);
        } catch {
            setError("Failed to update user");
        }
    };

    const handleDelete = async (username: string) => {
        if (!window.confirm("Delete this user?")) return;
        try {
            await deleteUserAccount(username);
            setUsers((u) => u.filter((x) => x.username !== username));
        } catch {
            setError("Failed to delete user");
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
                <div className="flex items-center justify-between mb-4">
                    <Title>👥 Manage Users</Title>
                    <Button variant="success" size="sm" onClick={() => { setShowCreate(true); setError(""); }}>
                        +
                    </Button>
                </div>
                <div className="mb-4">
                    <Link to="/admin-panel" className="text-blue-600 hover:underline">
                        ← Back to Dashboard
                    </Link>
                </div>
                {error && <Alert type="danger">{error}</Alert>}
                {skippedCount > 0 && (
                    <Alert type="warning">
                        {skippedCount} user(s) skipped due to missing or invalid username.
                    </Alert>
                )}
                <Card fit className="overflow-x-auto">
                    <div className="hidden sm:block">
                        <table className={`min-w-full border rounded-lg ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
                            <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
                                <tr>
                                    <th className="px-4 py-2 text-left">User</th>
                                    <th className="px-4 py-2 text-left">Skill Level</th>
                                    <th className="px-4 py-2 text-left">Created</th>
                                    <th className="px-4 py-2"></th>
                                </tr>
                            </thead>
                            <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
                                {validUsers.length === 0 ? (
                                    <tr>
                                        <td colSpan={4} className="px-4 py-6 text-center text-gray-400 italic">No user found.</td>
                                    </tr>
                                ) : (
                                    validUsers.map((u) => (
                                        <tr key={u.username} className={darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"}>
                                            <td className="px-4 py-2 font-semibold">{u.username}</td>
                                            <td className="px-4 py-2">{u.skill_level ?? "—"}</td>
                                            <td className="px-4 py-2">{u.created_at ? new Date(u.created_at).toLocaleString() : "—"}</td>
                                            <td className="px-4 py-2 flex gap-2">
                                                <Button size="auto" variant="secondary" onClick={() => setEditUser({ ...u, original: u.username })}>
                                                    Edit
                                                </Button>
                                                <Button size="auto" variant="danger" onClick={() => handleDelete(u.username)}>
                                                    Delete
                                                </Button>
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
                            <div className="px-4 py-6 text-center text-gray-400 italic">No user found.</div>
                        ) : (
                            validUsers.map((u) => (
                                <div key={u.username} className={`rounded-lg border p-4 flex flex-col gap-2 ${darkMode ? "bg-gray-900 border-gray-700" : "bg-white border-gray-200"}`}>
                                    <div><span className="font-semibold">User:</span> {u.username}</div>
                                    <div><span className="font-semibold">Skill Level:</span> {u.skill_level ?? "—"}</div>
                                    <div><span className="font-semibold">Created:</span> {u.created_at ? new Date(u.created_at).toLocaleString() : "—"}</div>
                                    <div className="flex gap-2 mt-2">
                                        <Button size="auto" variant="secondary" onClick={() => setEditUser({ ...u, original: u.username })}>
                                            Edit
                                        </Button>
                                        <Button size="auto" variant="danger" onClick={() => handleDelete(u.username)}>
                                            Delete
                                        </Button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </Card>
            </Container>

            {editUser && (
                <Modal onClose={() => setEditUser(null)}>
                    <h2 className="text-xl font-bold mb-4">Edit {editUser.original}</h2>
                    <Input
                        type="text"
                        value={editUser.username}
                        onChange={(e) => setEditUser({ ...editUser, username: e.target.value })}
                        className="mb-3"
                        placeholder="Username"
                    />
                    <Input
                        type="password"
                        placeholder="New Password"
                        onChange={(e) => setEditUser({ ...editUser, password: e.target.value })}
                        className="mb-3"
                    />
                    <Input
                        type="number"
                        value={editUser.skill_level ?? 0}
                        onChange={(e) => setEditUser({ ...editUser, skill_level: parseInt(e.target.value) })}
                        className="mb-4"
                    />
                    <div className="flex gap-2">
                        <Button variant="success" onClick={handleSave}>
                            Save
                        </Button>
                        <Button variant="secondary" onClick={() => setEditUser(null)}>
                            Cancel
                        </Button>
                    </div>
                </Modal>
            )}

            {showCreate && (
                <Modal onClose={() => { setShowCreate(false); setRepeatPassword(""); }}>
                    <h2 className="text-xl font-bold mb-4">Create New User</h2>
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
                        placeholder="Repeat Password"
                    />
                    {!passwordsMatch && repeatPassword && (
                        <Alert type="warning">Passwords do not match.</Alert>
                    )}
                    {error && <Alert type="danger">{error}</Alert>}
                    <div className="flex gap-2 mt-2">
                        <Button variant="success" onClick={handleCreate} disabled={!passwordsMatch}>
                            Create
                        </Button>
                        <Button variant="secondary" onClick={() => setShowCreate(false)}>
                            Cancel
                        </Button>
                    </div>
                </Modal>
            )}

            <Footer />
        </div>
    );
}


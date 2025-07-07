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

    return (
        <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>\
            <Container>
                <Title>👥 Manage Users</Title>
                <div className="mb-4">
                    <Link to="/admin-panel" className="text-blue-600 hover:underline">
                        ← Back to Dashboard
                    </Link>
                </div>
                {error && <Alert type="danger">{error}</Alert>}
                <Card fit className="overflow-x-auto">
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
                            {users.map((u) => (
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
                            ))}
                        </tbody>
                    </table>
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

            <Footer />
        </div>
    );
}


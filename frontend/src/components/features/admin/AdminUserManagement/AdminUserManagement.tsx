import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useRequireAdmin } from "../../../../hooks";
import { Container, Title } from "../../../common/UI/UI";
import Card from "../../../common/UI/Card";
import Button from "../../../common/UI/Button";
import Modal from "../../../common/UI/Modal";
import Alert from "../../../common/UI/Alert";
import useAppStore from "../../../../store/useAppStore";
import { fetchUsers, updateUserAccount, deleteUserAccount, signup } from "../../../../services/api";
import {
    Users,
    Plus,
    ArrowLeft,
} from "lucide-react";

// Import modular components
import UserTable from "./Tables/UserTable";
import CreateUserForm from "./Forms/CreateUserForm";
import EditUserForm from "./Forms/EditUserForm";

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
    const [isLoading, setIsLoading] = useState(false);
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
            setIsLoading(true);
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
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreate = async () => {
        try {
            setIsLoading(true);
            await signup(newUser.username, newUser.password);
            const data = await fetchUsers();
            const list = Array.isArray(data)
                ? data
                : Array.isArray(data?.users)
                    ? data.users
                    : [];
            setUsers(list);
            setShowCreate(false);
            setNewUser({ username: "", password: "", skill_level: 0 });
            setRepeatPassword("");
        } catch {
            setError("Failed to create user");
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!userToDelete) return;
        try {
            setIsLoading(true);
            await deleteUserAccount(userToDelete);
            const data = await fetchUsers();
            const list = Array.isArray(data)
                ? data
                : Array.isArray(data?.users)
                    ? data.users
                    : [];
            setUsers(list);
            setUserToDelete(null);
        } catch {
            setError("Failed to delete user");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Container>
            <div className="mb-6">
                <Link
                    to="/admin-panel"
                    className={`inline-flex items-center gap-2 mb-4 ${
                        darkMode ? "text-blue-400 hover:text-blue-300" : "text-blue-600 hover:text-blue-700"
                    }`}
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back to Admin Panel
                </Link>
                <Title>User Management</Title>
            </div>

            {error && <Alert variant="error" className="mb-4">{error}</Alert>}

            <div className="mb-6">
                <Button
                    onClick={() => setShowCreate(true)}
                    className="gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Add User
                </Button>
            </div>

            <Card>
                <UserTable
                    users={users}
                    darkMode={darkMode}
                    onEditUser={setEditUser}
                    onDeleteUser={setUserToDelete}
                />
            </Card>

            {/* Create User Modal */}
            {showCreate && (
                <Modal onClose={() => setShowCreate(false)}>
                    <div className="max-w-md mx-auto">
                        <h2 className="text-xl font-semibold mb-4">Create New User</h2>
                        <CreateUserForm
                            newUser={newUser}
                            setNewUser={setNewUser}
                            repeatPassword={repeatPassword}
                            setRepeatPassword={setRepeatPassword}
                            onSubmit={handleCreate}
                            onCancel={() => setShowCreate(false)}
                            isLoading={isLoading}
                        />
                    </div>
                </Modal>
            )}

            {/* Edit User Modal */}
            {editUser && (
                <Modal onClose={() => setEditUser(null)}>
                    <div className="max-w-md mx-auto">
                        <h2 className="text-xl font-semibold mb-4">Edit User</h2>
                        <EditUserForm
                            user={editUser}
                            setUser={setEditUser}
                            onSave={handleSave}
                            onCancel={() => setEditUser(null)}
                            isLoading={isLoading}
                        />
                    </div>
                </Modal>
            )}

            {/* Delete Confirmation Modal */}
            {userToDelete && (
                <Modal onClose={() => setUserToDelete(null)}>
                    <div className="text-center">
                        <h3 className="text-lg font-semibold mb-4">Confirm Deletion</h3>
                        <p className="mb-6">
                            Are you sure you want to delete user "{userToDelete}"?
                            This action cannot be undone.
                        </p>
                        <div className="flex gap-4 justify-center">
                            <Button
                                variant="danger"
                                onClick={handleDelete}
                                disabled={isLoading}
                            >
                                {isLoading ? "Deleting..." : "Delete"}
                            </Button>
                            <Button
                                variant="secondary"
                                onClick={() => setUserToDelete(null)}
                                disabled={isLoading}
                            >
                                Cancel
                            </Button>
                        </div>
                    </div>
                </Modal>
            )}
        </Container>
    );
}

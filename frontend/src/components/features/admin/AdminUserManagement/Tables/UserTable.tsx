import React from "react";
import { Link } from "react-router-dom";
import Button from "../../../../common/UI/Button";
import {
    Edit,
    Trash2,
    User,
    Target,
    Calendar,
    Shield
} from "lucide-react";

interface User {
    username: string;
    created_at?: string;
    skill_level?: number;
    password?: string;
    original?: string;
}

interface UserTableProps {
    users: User[];
    darkMode: boolean;
    onEditUser: (user: User) => void;
    onDeleteUser: (username: string) => void;
}

export default function UserTable({ users, darkMode, onEditUser, onDeleteUser }: UserTableProps) {
    return (
        <div className="overflow-x-auto">
            <table className={`min-w-full border rounded-lg overflow-hidden ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
                <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
                    <tr>
                        <th className="px-4 py-3 text-left font-semibold">Username</th>
                        <th className="px-4 py-3 text-left font-semibold">Level</th>
                        <th className="px-4 py-3 text-left font-semibold">Created</th>
                        <th className="px-4 py-3 text-left font-semibold">Actions</th>
                    </tr>
                </thead>
                <tbody className={darkMode ? "bg-gray-800 divide-gray-700" : "bg-white divide-gray-200"}>
                    {users.map((user) => (
                        <tr key={user.username} className={`${darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"} transition-colors`}>
                            <td className="px-4 py-3 font-semibold">{user.username}</td>
                            <td className="px-4 py-3">
                                <div className="flex items-center gap-2">
                                    <Target className="w-4 h-4 text-green-500" />
                                    {user.skill_level ?? "—"}
                                </div>
                            </td>
                            <td className="px-4 py-3">
                                <div className="flex items-center gap-2">
                                    <Calendar className="w-4 h-4 text-gray-400" />
                                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
                                </div>
                            </td>
                            <td className="px-4 py-3">
                                <div className="flex gap-2">
                                    <Link
                                        to="/profile-stats"
                                        state={{ username: user.username }}
                                        className={`inline-flex items-center gap-2 px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                                            darkMode
                                                ? "text-blue-400 hover:text-blue-300 hover:bg-gray-700"
                                                : "text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                        }`}
                                    >
                                        <Shield className="w-4 h-4" />
                                        View Stats
                                    </Link>
                                    <Button
                                        variant="ghost"
                                        size="auto"
                                        onClick={() => onEditUser(user)}
                                        className="p-2"
                                    >
                                        <Edit className="w-4 h-4" />
                                    </Button>
                                    <Button
                                        variant="danger"
                                        size="auto"
                                        onClick={() => onDeleteUser(user.username)}
                                        className="p-2"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

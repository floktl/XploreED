import { Link } from "react-router-dom";
import {
    Users,
    BarChart3,
    Calendar,
    Target
} from "lucide-react";

export default function UserManagement({
    results,
    darkMode
}) {
    return (
        <div className="mb-8">
            <div className="flex items-center gap-3 mb-6">
                <Users className={`w-6 h-6 ${darkMode ? "text-blue-400" : "text-blue-600"}`} />
                <h2 className="text-xl font-bold">User Management</h2>
            </div>
            <div className="overflow-x-auto">
                <table className={`min-w-full border rounded-lg overflow-hidden ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
                    <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
                        <tr>
                            <th className="px-4 py-3 text-left font-semibold">Username</th>
                            <th className="px-4 py-3 text-left font-semibold">Level</th>
                            <th className="px-4 py-3 text-left font-semibold">Last Activity</th>
                            <th className="px-4 py-3 text-left font-semibold">Actions</th>
                        </tr>
                    </thead>
                    <tbody className={darkMode ? "bg-gray-800 divide-gray-700" : "bg-white divide-gray-200"}>
                        {results.map((u) => (
                            <tr key={u.username} className={`${darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"} transition-colors`}>
                                <td className="px-4 py-3 font-semibold">{u.username}</td>
                                <td className="px-4 py-3">
                                    <div className="flex items-center gap-2">
                                        <Target className="w-4 h-4 text-green-500" />
                                        {u.lastLevel ?? "—"}
                                    </div>
                                </td>
                                <td className="px-4 py-3">
                                    <div className="flex items-center gap-2">
                                        <Calendar className="w-4 h-4 text-gray-400" />
                                        {u.lastTime ? new Date(u.lastTime).toLocaleString() : "—"}
                                    </div>
                                </td>
                                <td className="px-4 py-3">
                                    <Link
                                        to="/profile-stats"
                                        state={{ username: u.username }}
                                        className={`inline-flex items-center gap-2 px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                                            darkMode
                                                ? "text-blue-400 hover:text-blue-300 hover:bg-gray-700"
                                                : "text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                        }`}
                                    >
                                        <BarChart3 className="w-4 h-4" />
                                        View Stats
                                    </Link>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

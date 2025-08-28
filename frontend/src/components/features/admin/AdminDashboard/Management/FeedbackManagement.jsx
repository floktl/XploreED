import { MessageSquare } from "lucide-react";

export default function FeedbackManagement({
    supportFeedback,
    darkMode,
    handleDeleteFeedback
}) {
    return (
        <div className="mb-8">
            <div className="flex items-center gap-3 mb-4">
                <MessageSquare className={`w-6 h-6 ${darkMode ? "text-blue-400" : "text-blue-600"}`} />
                <h2 className="text-xl font-bold">User Feedback</h2>
            </div>
            {supportFeedback.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                    <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No feedback messages yet</p>
                </div>
            ) : (
                <div className="space-y-3 max-h-64 overflow-y-auto">
                    {supportFeedback.map((fb) => (
                        <div key={fb.id} className={`p-4 rounded-lg border ${darkMode ? "border-gray-600 bg-gray-700" : "border-gray-200 bg-gray-50"}`}>
                            <div className="flex justify-between items-start gap-3">
                                <p className="whitespace-pre-wrap mb-2 flex-1">{fb.message}</p>
                                <button
                                    onClick={() => handleDeleteFeedback(fb.id)}
                                    className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded ${darkMode ? "bg-red-600/20 text-red-300 hover:bg-red-600/30" : "bg-red-100 text-red-600 hover:bg-red-200"}`}
                                    title="Delete feedback"
                                >
                                    Delete
                                </button>
                            </div>
                            <div className="text-xs text-gray-500 mt-2">
                                From: {fb.username} • {new Date(fb.timestamp).toLocaleString()}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

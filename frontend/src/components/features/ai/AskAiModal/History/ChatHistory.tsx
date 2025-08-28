import React from "react";
import { User, Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatHistoryProps {
    history: Array<{
        id: number;
        question: string;
        answer: string;
        created_at: string;
    }>;
    darkMode: boolean;
}

export default function ChatHistory({ history, darkMode }: ChatHistoryProps) {
    if (history.length === 0) {
        return (
            <div className="text-center py-8 text-gray-500">
                <Bot className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No chat history yet. Start a conversation!</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {history.map((item) => (
                <div key={item.id} className="space-y-3">
                    {/* Question */}
                    <div className="flex gap-3">
                        <div className="flex-shrink-0">
                            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                                <User className="w-4 h-4 text-white" />
                            </div>
                        </div>
                        <div className="flex-1">
                            <div className={`p-3 rounded-lg ${darkMode ? "bg-gray-700" : "bg-gray-100"}`}>
                                <p className="text-sm">{item.question}</p>
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                                {new Date(item.created_at).toLocaleString()}
                            </div>
                        </div>
                    </div>

                    {/* Answer */}
                    <div className="flex gap-3">
                        <div className="flex-shrink-0">
                            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                                <Bot className="w-4 h-4 text-white" />
                            </div>
                        </div>
                        <div className="flex-1">
                            <div className={`p-3 rounded-lg ${darkMode ? "bg-gray-800" : "bg-white"} border ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    className="prose prose-sm max-w-none dark:prose-invert"
                                >
                                    {item.answer}
                                </ReactMarkdown>
                            </div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

import React from "react";
import { User, Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Spinner from "../../../../common/UI/Spinner";

interface AnswerBlock {
    type: string;
    text: string;
}

interface CurrentChatProps {
    question: string;
    answerBlocks: AnswerBlock[];
    loading: boolean;
    darkMode: boolean;
}

export default function CurrentChat({ question, answerBlocks, loading, darkMode }: CurrentChatProps) {
    if (!question && answerBlocks.length === 0 && !loading) {
        return null;
    }

    return (
        <div className="space-y-3">
            {/* Current Question */}
            {question && (
                <div className="flex gap-3">
                    <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                            <User className="w-4 h-4 text-white" />
                        </div>
                    </div>
                    <div className="flex-1">
                        <div className={`p-3 rounded-lg ${darkMode ? "bg-gray-700" : "bg-gray-100"}`}>
                            <p className="text-sm">{question}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Current Answer */}
            {answerBlocks.length > 0 && (
                <div className="flex gap-3">
                    <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                            <Bot className="w-4 h-4 text-white" />
                        </div>
                    </div>
                    <div className="flex-1">
                        <div className={`p-3 rounded-lg ${darkMode ? "bg-gray-800" : "bg-white"} border ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
                            {answerBlocks.map((block, index) => (
                                <div key={index}>
                                    {block.type === "text" && (
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            className="prose prose-sm max-w-none dark:prose-invert"
                                        >
                                            {block.text}
                                        </ReactMarkdown>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Loading Spinner */}
            {loading && (
                <div className="flex gap-3">
                    <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                            <Bot className="w-4 h-4 text-white" />
                        </div>
                    </div>
                    <div className="flex-1">
                        <div className={`p-3 rounded-lg ${darkMode ? "bg-gray-800" : "bg-white"} border ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
                            <div className="flex items-center gap-2">
                                <Spinner />
                                <span className="text-sm text-gray-500">AI is thinking...</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

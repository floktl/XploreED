import React, { useRef, useState } from "react";
import Button from "../../../../common/UI/Button";
import { Send } from "lucide-react";

interface ChatInputProps {
    question: string;
    setQuestion: (question: string) => void;
    onAsk: () => void;
    loading: boolean;
    error: string;
}

export default function ChatInput({ question, setQuestion, onAsk, loading, error }: ChatInputProps) {
    const inputRef = useRef<HTMLInputElement>(null);
    const [cursorPosition, setCursorPosition] = useState(0);

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onAsk();
        }
    };

    return (
        <div className="flex gap-3">
            <div className="flex-1 relative">
                {/* Chat bubble input field */}
                <div className="relative">
                    <input
                        ref={inputRef}
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyPress={handleKeyPress}
                        onSelect={(e) => {
                            const target = e.target as HTMLInputElement;
                            setCursorPosition(target.selectionStart || 0);
                        }}
                        onMouseUp={(e) => {
                            const target = e.target as HTMLInputElement;
                            setCursorPosition(target.selectionStart || 0);
                        }}
                        placeholder="Ask me anything about German learning..."
                        className="w-full px-4 py-3 bg-gray-700 dark:bg-gray-600 border-0 rounded-2xl text-white text-base placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200 relative"
                        disabled={loading}
                    />
                    {/* Cursor indicator */}
                    <div
                        className="absolute top-1/2 transform -translate-y-1/2 w-0.5 h-5 bg-blue-400 animate-pulse pointer-events-none transition-all duration-100"
                        style={{
                            left: `${Math.min(cursorPosition * 8 + 16, 100)}px`,
                            opacity: cursorPosition > 0 ? 1 : 0
                        }}
                    />
                </div>
                {error && (
                    <div className="absolute -bottom-6 left-0 text-red-500 text-sm">
                        {error}
                    </div>
                )}
            </div>
            <Button
                onClick={onAsk}
                disabled={loading || !question.trim()}
                className="px-6 py-3 rounded-2xl gap-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 transition-all duration-200"
            >
                <Send className="w-4 h-4" />
                {loading ? "Asking..." : "Ask"}
            </Button>
        </div>
    );
}

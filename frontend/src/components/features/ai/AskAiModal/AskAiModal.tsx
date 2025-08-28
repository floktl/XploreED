import React, { useState, useEffect, useRef } from "react";
import Modal from "../../../common/UI/Modal";
import { Lightbulb } from "lucide-react";
import { getMistralChatHistory, addMistralChatHistory } from "../../../../services/api";
import useAppStore from "../../../../store/useAppStore";

// Import modular components
import ChatInput from "./Input/ChatInput";
import ChatHistory from "./History/ChatHistory";
import CurrentChat from "./Chat/CurrentChat";

interface Props {
    onClose: () => void;
    btnRect?: DOMRect | null;
}

interface AnswerBlock {
    type: string;
    text: string;
}

interface ChatHistory {
    id: number;
    question: string;
    answer: string;
    created_at: string;
}

export default function AskAiModal({ onClose, btnRect }: Props) {
    const [question, setQuestion] = useState(() => localStorage.getItem('aiChatInput') || "");
    const [answerBlocks, setAnswerBlocks] = useState<AnswerBlock[]>([]);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [history, setHistory] = useState<ChatHistory[]>([]);
    const chatEndRef = useRef<HTMLDivElement>(null);
    const currentPageContent = useAppStore((s) => s.currentPageContent);
    const darkMode = useAppStore((s) => s.darkMode);

    // Load history from backend on mount
    useEffect(() => {
        const loadHistory = async () => {
            try {
                const h = await getMistralChatHistory();
                setHistory(h);
            } catch (err) {
                console.error("Failed to load chat history:", err);
            }
        };
        loadHistory();
    }, []);

    // Scroll to bottom only when a new question is asked (first block of answerBlocks)
    useEffect(() => {
        if (answerBlocks.length === 1 && chatEndRef.current) {
            chatEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [answerBlocks]);

    // Save input to localStorage on change
    useEffect(() => {
        localStorage.setItem('aiChatInput', question);
    }, [question]);

    // Always scroll chat to bottom when modal is opened or history changes
    useEffect(() => {
        if (chatEndRef.current) {
            chatEndRef.current.scrollIntoView({ behavior: "auto" });
        }
    }, [history]);

    const handleAsk = async () => {
        if (!question.trim()) {
            setError("Please enter a question.");
            return;
        }

        try {
            setLoading(true);
            setError("");

            // Scroll to bottom so spinner is visible
            setTimeout(() => {
                if (chatEndRef.current) {
                    chatEndRef.current.scrollIntoView({ behavior: "smooth" });
                }
            }, 0);

            // Send question to backend and get full answer, always include context if available
            const res = await fetch("/api/ask-ai-context", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify(currentPageContent ? { question, context: currentPageContent } : { question }),
            });
            const data = await res.json();

            if (data.answer && data.answer.trim()) {
                setAnswerBlocks([{ type: "text", text: data.answer }]);

                // Add to history
                try {
                    await addMistralChatHistory(question, data.answer);
                    const updatedHistory = await getMistralChatHistory();
                    setHistory(updatedHistory);
                } catch (err) {
                    console.error("Failed to save chat history:", err);
                }
            } else {
                setError("No answer received from AI.");
            }
        } catch (err) {
            console.error("Failed to ask AI:", err);
            setError("Failed to get answer. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal onClose={onClose}>
            <div className="max-w-4xl w-full max-h-[80vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                        <Lightbulb className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold">AI Learning Assistant</h2>
                        <p className="text-sm text-gray-500">Ask me anything about German learning!</p>
                    </div>
                </div>

                {/* Chat Area */}
                <div className="flex-1 overflow-y-auto mb-4 space-y-6">
                    {/* Chat History */}
                    <ChatHistory history={history} darkMode={darkMode} />

                    {/* Current Chat */}
                    <CurrentChat
                        question={question}
                        answerBlocks={answerBlocks}
                        loading={loading}
                        darkMode={darkMode}
                    />

                    <div ref={chatEndRef} />
                </div>

                {/* Input Area */}
                <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                    <ChatInput
                        question={question}
                        setQuestion={setQuestion}
                        onAsk={handleAsk}
                        loading={loading}
                        error={error}
                    />
                </div>
            </div>
        </Modal>
    );
}

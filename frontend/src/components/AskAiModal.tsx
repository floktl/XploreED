import React, { useState, useEffect, useRef } from "react";
import Modal from "./UI/Modal";
import Button from "./UI/Button";
import Spinner from "./UI/Spinner";
import { Lightbulb, User, Bot, Send } from "lucide-react";
import { streamAiAnswer } from "../utils/streamAi";
import { getMistralChatHistory, addMistralChatHistory } from "../api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
    onClose: () => void;
    btnRect?: DOMRect | null;
    pageContext?: any;
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

export default function AskAiModal({ onClose, btnRect, pageContext }: Props) {
    const [question, setQuestion] = useState("");
    const [answerBlocks, setAnswerBlocks] = useState<AnswerBlock[]>([]);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [history, setHistory] = useState<ChatHistory[]>([]);
    const chatEndRef = useRef<HTMLDivElement>(null);
    const fullAnswerRef = useRef("");
    const [isStreaming, setIsStreaming] = useState(false);

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

    // Scroll to bottom when history is loaded (on open)
    useEffect(() => {
      if (history.length > 0 && chatEndRef.current) {
        chatEndRef.current.scrollIntoView({ behavior: "auto" });
      }
    }, [history.length]);


    const handleAsk = async () => {
        if (!question.trim()) {
            setError("Please enter a question.");
            return;
        }

        try {
            setLoading(true);
            setIsStreaming(true);
            setAnswerBlocks([]);
            fullAnswerRef.current = "";

            await streamAiAnswer(question.trim(), (chunk) => {
                fullAnswerRef.current = chunk.text;
                setAnswerBlocks([{ type: 'paragraph', text: chunk.text }]);
            }, pageContext);

            setIsStreaming(false);

            // After streaming, if no answer, show placeholder
            if (!fullAnswerRef.current.trim()) {
                setAnswerBlocks([{ type: "paragraph", text: "[No answer returned by AI]" }]);
            }

            // Save to backend history
            try {
                await addMistralChatHistory(question.trim(), fullAnswerRef.current);
                // Reload history
                const h = await getMistralChatHistory();
                setHistory(h);
            } catch (err) {
                console.error("Failed to save chat history:", err);
            }

            setError("");
        } catch (err) {
            console.error("❌ AI streaming error:", err);
            setError("Failed to get answer.");
        } finally {
            setLoading(false);
            setQuestion("");
        }
    };

    // Calculate modal position for speech bubble
    let modalStyle: React.CSSProperties = {
        position: "fixed",
        zIndex: 100,
        maxWidth: "min(400px, 96vw)",
        width: "96vw",
        left: '50%',
        transform: 'translateX(-50%)',
        border: "none",
        boxShadow: "0 8px 32px rgba(0,0,0,0.18)",
        background: "rgba(255,255,255,0.38)",
        backdropFilter: "blur(18px)",
        WebkitBackdropFilter: "blur(18px)",
        borderRadius: 24,
        padding: 0,
        maxHeight: "80vh",
        display: "flex",
        flexDirection: "column",
    };
    let arrowStyle: React.CSSProperties = {};
    if (btnRect) {
        // Center modal horizontally above the button, and place tail at the bottom center
        modalStyle.bottom = window.innerHeight - btnRect.top + 56;
        arrowStyle = {
            position: "absolute",
            left: "50%",
            transform: "translateX(-50%)",
            top: "100%",
            width: 48,
            height: 24,
            zIndex: 101,
            pointerEvents: 'none',
        };
    }

    return (
        <>
            {/* Darkened, blurred background overlay */}
            <div className="fixed inset-0 z-40 bg-black bg-opacity-20 backdrop-blur-[2px]" />
            <div style={modalStyle} className="z-50 animate-fade-in rounded-2xl overflow-visible border border-white/30 shadow-xl relative">
                <div className="relative text-gray-900 flex flex-col" style={{overflow: 'hidden'}}>
                {/* Header */}
                <div className="flex items-center justify-between px-4 pt-3 pb-2 border-b border-white/30 min-h-[44px]">
                    <div className="flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-blue-400" />
                        <span className="font-bold text-lg whitespace-nowrap">Ask Mistral AI</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" onClick={onClose}>✕</Button>
                    </div>
                </div>
                {/* Chat area: show all history as a continuous chat */}
                <div className="flex-1 overflow-y-auto px-3 sm:px-4 py-3 space-y-2 sm:space-y-3 max-h-64 min-h-[120px]" style={{background: "rgba(255,255,255,0.13)"}}>
                    {history.length === 0 && answerBlocks.length === 0 && (
                        <div className="text-gray-400 italic text-center pt-6 text-sm sm:text-base">Ask anything about German or your learning progress!</div>
                    )}
                    {/* Render all previous chat history */}
                    {history.slice().reverse().map((h) => (
                        <React.Fragment key={h.id}>
                            {/* User bubble */}
                            <div className="flex items-end gap-1 sm:gap-2 justify-end w-full">
                                <div className="flex items-end gap-1 sm:gap-2 w-full justify-end">
                                    <div className="relative max-w-[75%] sm:max-w-[70%] flex items-end">
                                        <div className="bg-blue-500 text-white rounded-2xl px-3 sm:px-4 py-2 shadow text-sm relative chat-bubble-user flex items-center min-h-[36px]" style={{backdropFilter: 'blur(2px)'}}>
                                            {h.question}
                                            <span className="absolute right-[-10px] bottom-0 w-0 h-0 border-t-[12px] border-t-blue-500 border-l-[12px] border-l-transparent border-b-0 border-r-0" />
                                        </div>
                                    </div>
                                    <div className="rounded-full bg-blue-500 w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center text-white font-bold shadow"><User className="w-4 h-4 sm:w-5 sm:h-5" /></div>
                                </div>
                            </div>
                            {/* AI bubble */}
                            <div className="flex items-end gap-1 sm:gap-2 justify-start w-full">
                                <div className="flex items-end gap-1 sm:gap-2 w-full justify-start">
                                    <div className="rounded-full bg-blue-900 w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center text-white font-bold shadow"><Bot className="w-4 h-4 sm:w-5 sm:h-5" /></div>
                                    <div className="relative w-full" style={{maxWidth: 480, margin: '0 auto'}}>
                                        <div
                                            className="bg-white/40 text-gray-900 rounded-2xl px-3 sm:px-4 py-2 shadow text-sm relative chat-bubble-ai min-h-[36px] w-full"
                                            style={{
                                                backdropFilter: 'blur(6px)',
                                                WebkitBackdropFilter: 'blur(6px)',
                                                background: 'rgba(255,255,255,0.75)',
                                                border: '1.5px solid #e0e7ef',
                                                boxShadow: '0 2px 12px 0 rgba(80,120,200,0.07)',
                                                fontSize: '0.95rem',
                                                fontFamily: 'Inter, Segoe UI, system-ui, sans-serif',
                                                color: '#1a237e',
                                                lineHeight: 1.5,
                                                wordBreak: 'break-word',
                                                whiteSpace: undefined, // Remove pre-line from the bubble
                                                margin: '6px 0 10px 0',
                                                padding: '14px 16px',
                                                borderRadius: '20px',
                                                maxWidth: '100%',
                                            }}
                                        >
                                            {typeof h.answer === 'string' && (
                                                <ReactMarkdown
                                                    children={h.answer}
                                                    remarkPlugins={[remarkGfm]}
                                                    components={{
                                                        h1: ({node, ...props}) => <h1 className="font-bold text-lg mt-2 mb-1" {...props} />,
                                                        h2: ({node, ...props}) => <h2 className="font-bold text-base mt-2 mb-1" {...props} />,
                                                        h3: ({node, ...props}) => <h3 className="font-semibold text-base mt-2 mb-1" {...props} />,
                                                        strong: ({node, ...props}) => <strong className="font-bold text-blue-900" {...props} />,
                                                        em: ({node, ...props}) => <em className="italic text-blue-700" {...props} />,
                                                        table: ({node, ...props}) => <div className="markdown-table-wrapper"><table className="border border-blue-200 my-2" {...props} /></div>,
                                                        th: ({isHeader, node, ...props}) => <th className="border px-2 py-1 bg-blue-50" {...props} />,
                                                        td: ({isHeader, node, ...props}) => <td className="border px-2 py-1" {...props} />,
                                                        ul: ({ordered, node, ...props}) => <ul className="list-disc ml-6 my-2" {...props} />,
                                                        ol: ({ordered, node, ...props}) => <ol className="list-decimal ml-6 my-2" {...props} />,
                                                        li: ({ordered, node, ...props}) => <li className="mb-1" {...props} />,
                                                        p: ({node, ...props}) => <p style={{whiteSpace: 'pre-line'}} {...props} />,
                                                        blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-blue-200 pl-3 italic text-blue-800 my-2" style={{whiteSpace: 'pre-line'}} {...props} />,
                                                    }}
                                                />
                                            )}
                                            <span className="absolute left-[-10px] bottom-0 w-0 h-0 border-t-[12px] border-t-white/70 border-r-[12px] border-r-transparent border-b-0 border-l-0" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </React.Fragment>
                    ))}
                    {/* Render current question/answer if present */}
                    {answerBlocks.length > 0 && (
                        <div className="flex flex-col gap-2 sm:gap-3 w-full">
                            {/* User bubble */}
                            <div className="flex items-end gap-1 sm:gap-2 justify-end w-full">
                                <div className="flex items-end gap-1 sm:gap-2 w-full justify-end">
                                    <div className="relative max-w-[75%] sm:max-w-[70%] flex items-end">
                                        <div className="bg-blue-500 text-white rounded-2xl px-3 sm:px-4 py-2 shadow text-sm relative chat-bubble-user flex items-center min-h-[36px]" style={{backdropFilter: 'blur(2px)'}}>
                                            {question}
                                            <span className="absolute right-[-10px] bottom-0 w-0 h-0 border-t-[12px] border-t-blue-500 border-l-[12px] border-l-transparent border-b-0 border-r-0" />
                                        </div>
                                    </div>
                                    <div className="rounded-full bg-blue-500 w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center text-white font-bold shadow"><User className="w-4 h-4 sm:w-5 sm:h-5" /></div>
                                </div>
                            </div>
                            {/* AI bubbles */}
                            {answerBlocks.map((block, idx) => (
                                <div key={idx} className="flex items-end gap-1 sm:gap-2 justify-start w-full">
                                    <div className="flex items-end gap-1 sm:gap-2 w-full justify-start">
                                        <div className="rounded-full bg-blue-900 w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center text-white font-bold shadow"><Bot className="w-4 h-4 sm:w-5 sm:h-5" /></div>
                                        <div className="relative w-full" style={{maxWidth: 480, margin: '0 auto'}}>
                                            <div
                                                className="bg-white/40 text-gray-900 rounded-2xl px-3 sm:px-4 py-2 shadow text-sm relative chat-bubble-ai min-h-[36px] w-full"
                                                style={{
                                                    backdropFilter: 'blur(6px)',
                                                    WebkitBackdropFilter: 'blur(6px)',
                                                    background: 'rgba(255,255,255,0.75)',
                                                    border: '1.5px solid #e0e7ef',
                                                    boxShadow: '0 2px 12px 0 rgba(80,120,200,0.07)',
                                                    fontSize: '0.95rem',
                                                    fontFamily: 'Inter, Segoe UI, system-ui, sans-serif',
                                                    color: '#1a237e',
                                                    lineHeight: 1.5,
                                                    wordBreak: 'break-word',
                                                    whiteSpace: undefined, // Remove pre-line from the bubble
                                                    margin: '6px 0 10px 0',
                                                    padding: '14px 16px',
                                                    borderRadius: '20px',
                                                    maxWidth: '100%',
                                                }}
                                            >
                                                <ReactMarkdown
                                                    children={block.text}
                                                    remarkPlugins={[remarkGfm]}
                                                    components={{
                                                        h1: ({node, ...props}) => <h1 className="font-bold text-lg mt-2 mb-1" {...props} />,
                                                        h2: ({node, ...props}) => <h2 className="font-bold text-base mt-2 mb-1" {...props} />,
                                                        h3: ({node, ...props}) => <h3 className="font-semibold text-base mt-2 mb-1" {...props} />,
                                                        strong: ({node, ...props}) => <strong className="font-bold text-blue-900" {...props} />,
                                                        em: ({node, ...props}) => <em className="italic text-blue-700" {...props} />,
                                                        table: ({node, ...props}) => <div className="markdown-table-wrapper"><table className="border border-blue-200 my-2" {...props} /></div>,
                                                        th: ({isHeader, node, ...props}) => <th className="border px-2 py-1 bg-blue-50" {...props} />,
                                                        td: ({isHeader, node, ...props}) => <td className="border px-2 py-1" {...props} />,
                                                        ul: ({ordered, node, ...props}) => <ul className="list-disc ml-6 my-2" {...props} />,
                                                        ol: ({ordered, node, ...props}) => <ol className="list-decimal ml-6 my-2" {...props} />,
                                                        li: ({ordered, node, ...props}) => <li className="mb-1" {...props} />,
                                                        p: ({node, ...props}) => <p style={{whiteSpace: 'pre-line'}} {...props} />,
                                                        blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-blue-200 pl-3 italic text-blue-800 my-2" {...props} />,
                                                    }}
                                                />
                                                <span className="absolute left-[-10px] bottom-0 w-0 h-0 border-t-[12px] border-t-white/70 border-r-[12px] border-r-transparent border-b-0 border-l-0" />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>
                {/* Input area */}
                <form className="flex items-center gap-2 px-3 sm:px-4 py-3 border-t border-white/30 bg-transparent" onSubmit={e => { e.preventDefault(); handleAsk(); }}>
                    <div className="flex-1 flex items-center bg-white/45 rounded-full shadow border border-blue-100 px-3 py-1" style={{backdropFilter: 'blur(8px)'}}>
                        <textarea
                            className="flex-1 h-10 sm:h-11 max-h-20 min-h-[40px] sm:min-h-[44px] bg-transparent text-gray-900 resize-none focus:ring-0 focus:outline-none placeholder-gray-500 border-0 p-0 m-0 align-middle text-sm sm:text-base"
                            placeholder="Type your question..."
                            value={question}
                            onChange={(e) => setQuestion(e.target.value)}
                            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleAsk(); } }}
                            style={{boxShadow: 'none'}}
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading || !question.trim()}
                        className={`ml-2 flex items-center justify-center rounded-full w-10 h-10 sm:w-12 sm:h-12 shadow-lg transition-all duration-150 ${loading || !question.trim() ? 'bg-blue-200 text-white' : 'bg-blue-500 hover:bg-blue-600 text-white'} focus:outline-none focus:ring-2 focus:ring-blue-400`}
                        style={{minWidth: 40, minHeight: 40}}
                        aria-label="Ask"
                    >
                        <Send className="w-5 h-5 sm:w-6 sm:h-6" />
                    </button>
                </form>
                {/* Speech bubble tail (unified with modal) */}
                {btnRect && (
                    <svg style={arrowStyle} viewBox="0 0 48 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M0 0 Q24 32 48 0" fill="rgba(255,255,255,0.38)" filter="url(#shadow)" />
                        <filter id="shadow" x="-10" y="0" width="68" height="34">
                            <feDropShadow dx="0" dy="2" stdDeviation="2" floodColor="#000" floodOpacity="0.10" />
                        </filter>
                    </svg>
                )}
                </div>
            </div>
        </>
    );
}

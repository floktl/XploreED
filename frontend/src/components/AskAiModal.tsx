import React, { useState, useEffect, useRef } from "react";
import Modal from "./UI/Modal";
import Button from "./UI/Button";
import Spinner from "./UI/Spinner";
import { Lightbulb, User, Bot, Send } from "lucide-react";
import { streamAiAnswer } from "../utils/streamAi";
import { getMistralChatHistory, addMistralChatHistory } from "../api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import useAppStore from "../store/useAppStore";

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
                // Check if AI requests context (special string)
                if (data.answer.includes("__REQUEST_CONTEXT__")) {
                    // Send current page content as context
                    if (currentPageContent) {
                        const contextRes = await fetch("/api/ask-ai-context", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            credentials: "include",
                            body: JSON.stringify({ question, context: currentPageContent }),
                        });
                        const contextData = await contextRes.json();
                        if (contextData.answer && contextData.answer.trim()) {
                            await fetch("/api/mistral-chat-history", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                credentials: "include",
                                body: JSON.stringify({ question, answer: contextData.answer }),
                            });
                            const h = await getMistralChatHistory();
                            setHistory(h);
                            setQuestion("");
                        } else {
                            setError("No answer received from AI after sending context.");
                        }
                    } else {
                        setError("AI requested context, but no page content is available.");
                    }
                } else {
                    // Save to backend history
                    await fetch("/api/mistral-chat-history", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        credentials: "include",
                        body: JSON.stringify({ question, answer: data.answer }),
                    });
                    // Reload history
                    const h = await getMistralChatHistory();
                    setHistory(h);
                    setQuestion("");
                }
            } else {
                setError("No answer received from AI.");
            }
        } catch (err) {
            setError("Failed to get answer from AI.");
        } finally {
            setLoading(false);
        }
    };

    // Calculate modal position for speech bubble
    let modalStyle: React.CSSProperties = {
        position: "fixed",
        zIndex: 100,
        maxWidth: "min(600px, 98vw)",
        width: "98vw",
        left: '50%',
        transform: 'translateX(-50%)',
        top: '64px', // leave space for header
        bottom: '64px', // leave space for footer
        border: "none",
        boxShadow: "0 8px 32px rgba(0,0,0,0.18)",
        background: "transparent", // fully transparent
        backdropFilter: "blur(18px)",
        WebkitBackdropFilter: "blur(18px)",
        borderRadius: 24,
        padding: 0,
        maxHeight: "calc(100vh - 128px)",
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
            <div className="fixed inset-0 z-40" style={{background: "rgba(20,20,30,0.55)", backdropFilter: "blur(3px)"}} onClick={onClose} />
            <div style={{
                ...modalStyle,
                background: darkMode ? 'rgba(10,16,32,0.98)' : 'transparent',
            }} className="z-50 animate-fade-in rounded-2xl overflow-visible border border-white/30 shadow-xl relative" onClick={e => e.stopPropagation()}>
                {/* Small red X close button */}
                <button
                    onClick={onClose}
                    aria-label="Close"
                    style={{
                        position: 'absolute',
                        top: 10,
                        right: 14,
                        width: 28,
                        height: 28,
                        borderRadius: '50%',
                        background: '#e11d48', // Tailwind rose-600
                        color: '#fff',
                        border: 'none',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: 18,
                        boxShadow: '0 2px 8px rgba(0,0,0,0.10)',
                        zIndex: 200
                    }}
                >
                    ×
                </button>
                <div className="relative text-gray-900 flex flex-col" style={{overflow: 'hidden'}}>
                {/* Header */}
                {/* Remove the modal header area:
                <div className="flex items-center justify-between px-4 pt-3 pb-2 border-b border-white/30 min-h-[44px]">
                    <div className="flex items-center gap-2">
                        <Lightbulb className="w-5 h-5 text-blue-400" />
                        <span className="font-bold text-lg whitespace-nowrap">Ask Mistral AI</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Button variant="ghost" size="sm" onClick={onClose}>✕</Button>
                    </div>
                </div>
                */}
                {/* Chat area: show all history as a continuous chat */}
                <div className="flex-1 overflow-y-auto px-3 sm:px-4 py-3 space-y-2 sm:space-y-3 max-h-[60vh] min-h-[120px]" style={{background: "transparent"}}>
                    {history.length === 0 && (
                        <div className="text-gray-400 italic text-center pt-6 text-sm sm:text-base">Ask anything about German or your learning progress!</div>
                    )}
                    {/* Render all previous chat history */}
                    {history.slice().reverse().map((h) => (
                        <React.Fragment key={h.id}>
                            {/* User bubble */}
                            <div className="flex items-end gap-1 sm:gap-2 justify-end w-full">
                                <div className="flex items-end gap-1 sm:gap-2 w-full justify-end">
                                    <div className="relative max-w-[75%] sm:max-w-[70%] flex items-end">
                                        <div className="rounded-2xl px-3 sm:px-4 py-2 text-sm relative chat-bubble-user flex items-center min-h-[36px]"
                                            style={{
                                                background: darkMode ? '#22304a' : 'rgba(30,60,120,0.92)',
                                                color: darkMode ? '#f8fafc' : '#e0e7ef',
                                                borderRadius: 20,
                                                boxShadow: '0 2px 12px 0 rgba(30,60,120,0.18)',
                                                backdropFilter: 'blur(2px)'
                                            }}>
                                            {h.question}
                                        </div>
                                    </div>
                                    <div className="rounded-full bg-blue-500 w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center text-white font-bold shadow"><User className="w-4 h-4 sm:w-5 sm:h-5" /></div>
                                </div>
                            </div>
                            {/* AI bubble */}
                            <div className="flex items-end gap-1 sm:gap-2 justify-start w-full">
                                <div className="flex items-end gap-1 sm:gap-2 w-full justify-start">
                                    <div className="rounded-full bg-blue-900 w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center text-white font-bold shadow"><Bot className="w-4 h-4 sm:w-5 sm:h-5" /></div>
                                    <div className="relative w-full flex justify-center" style={{maxWidth: 480, margin: '0 auto'}}>
                                        <div
                                            className="rounded-2xl px-3 sm:px-4 py-2 text-sm relative chat-bubble-ai min-h-[36px]"
                                            style={{
                                                display: 'flex',
                                                flexDirection: 'column',
                                                alignItems: 'flex-start',
                                                justifyContent: 'center',
                                                textAlign: 'left',
                                                backdropFilter: 'blur(6px)',
                                                WebkitBackdropFilter: 'blur(6px)',
                                                background: darkMode ? '#181f2a' : 'rgba(40,44,60,0.92)',
                                                color: darkMode ? '#f8fafc' : '#f3f4f6',
                                                borderRadius: 20,
                                                boxShadow: '0 2px 12px 0 rgba(40,44,60,0.18)',
                                                fontSize: '0.95rem',
                                                fontFamily: 'Inter, Segoe UI, system-ui, sans-serif',
                                                lineHeight: 1.5,
                                                wordBreak: 'break-word',
                                                margin: '6px 0 10px 0',
                                                padding: '14px 16px',
                                                maxWidth: 480,
                                                width: '100%',
                                                boxSizing: 'border-box',
                                                overflow: 'visible',
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
                                                        table: ({node, ...props}) => (
                                                            <div className="markdown-table-wrapper" style={{overflowX: 'auto'}}>
                                                                <table
                                                                    className="border my-2"
                                                                    style={{
                                                                        background: darkMode ? '#1a2332' : '#fff',
                                                                        color: darkMode ? '#f8fafc' : '#222',
                                                                        borderCollapse: 'collapse',
                                                                        width: '100%'
                                                                    }}
                                                                    {...props}
                                                                />
                                                            </div>
                                                        ),
                                                        th: ({node, ...props}) => (
                                                            <th
                                                                className="border px-2 py-0.5"
                                                                style={{
                                                                    background: darkMode ? '#22304a' : '#e0e7ef',
                                                                    color: darkMode ? '#f8fafc' : '#222',
                                                                    fontWeight: 700,
                                                                    verticalAlign: 'middle',
                                                                    textAlign: 'center'
                                                                }}
                                                                {...props}
                                                            />
                                                        ),
                                                        td: ({node, ...props}) => (
                                                            <td
                                                                className="border px-2 py-0.5"
                                                                style={{
                                                                    background: darkMode ? '#1a2332' : '#fff',
                                                                    color: darkMode ? '#f8fafc' : '#222',
                                                                    verticalAlign: 'middle',
                                                                    textAlign: 'center'
                                                                }}
                                                                {...props}
                                                            />
                                                        ),
                                                        ul: ({node, ...props}) => <ul className="list-disc ml-6 my-2" {...props} />,
                                                        ol: ({node, ...props}) => <ol className="list-decimal ml-6 my-2" {...props} />,
                                                        li: ({node, ...props}) => {
                                                            // Remove 'index' and any other non-standard props
                                                            const { index, ...rest } = props;
                                                            return <li className="mb-1" {...rest} />;
                                                        },
                                                        p: ({node, ...props}) => <p style={{whiteSpace: 'pre-line'}} {...props} />,
                                                        blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-blue-200 pl-3 italic text-blue-800 my-2" {...props} />,
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
                                        <div className="relative w-full flex justify-center" style={{maxWidth: 480, margin: '0 auto'}}>
                                            <div
                                                className="bg-white/40 text-gray-900 rounded-2xl px-3 sm:px-4 py-2 shadow text-sm relative chat-bubble-ai min-h-[36px]"
                                                style={{
                                                    display: 'flex',
                                                    flexDirection: 'column',
                                                    alignItems: 'flex-start', // left-align content
                                                    justifyContent: 'center',
                                                    textAlign: 'left', // left-align text
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
                                                    whiteSpace: undefined,
                                                    margin: '6px 0 10px 0',
                                                    padding: '14px 16px',
                                                    borderRadius: '20px',
                                                    maxWidth: 480,
                                                    width: '100%',
                                                    boxSizing: 'border-box',
                                                    maxHeight: undefined,
                                                    overflow: 'visible',
                                                }}
                                            >
                                                {typeof block.text === 'string' && (
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
                                                            th: ({node, ...props}) => (
                                                                <th
                                                                    className="border px-1 py-0"
                                                                    style={{
                                                                        background: darkMode ? '#2563EB' : '#e0e7ef', // match send button blue-700
                                                                        color: darkMode ? '#2563EB' : '#222',
                                                                        fontWeight: 700,
                                                                        verticalAlign: 'middle',
                                                                        textAlign: 'center',
                                                                        fontSize: 12,
                                                                        lineHeight: 1.1
                                                                    }}
                                                                    {...props}
                                                                />
                                                            ),
                                                            td: ({node, ...props}) => (
                                                                <td
                                                                    className="border px-1 py-0"
                                                                    style={{
                                                                        background: darkMode ? '#1a2332' : '#fff',
                                                                        color: darkMode ? '#f8fafc' : '#222',
                                                                        verticalAlign: 'middle',
                                                                        textAlign: 'center',
                                                                        fontSize: 12,
                                                                        lineHeight: 1.1
                                                                    }}
                                                                    {...props}
                                                                />
                                                            ),
                                                            ul: ({node, ...props}) => <ul className="list-disc ml-6 my-2" {...props} />,
                                                            ol: ({node, ...props}) => <ol className="list-decimal ml-6 my-2" {...props} />,
                                                            li: ({node, ...props}) => {
                                                                // Remove 'index' and any other non-standard props
                                                                const { index, ...rest } = props;
                                                                return <li className="mb-1" {...rest} />;
                                                            },
                                                            p: ({node, ...props}) => <p style={{whiteSpace: 'pre-line'}} {...props} />,
                                                            blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-blue-200 pl-3 italic text-blue-800 my-2" {...props} />,
                                                        }}
                                                    />
                                                )}
                                                <span className="absolute left-[-10px] bottom-0 w-0 h-0 border-t-[12px] border-t-white/70 border-r-[12px] border-r-transparent border-b-0 border-l-0" />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                    {/* Spinner while loading */}
                    {loading && (
                        <div className="flex justify-center items-center py-4">
                            <Spinner />
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>
                {/* Input area */}
                <form className="flex items-center gap-2 px-3 sm:px-4 py-3 border-t border-white/30 bg-transparent" style={{background: 'rgba(30,32,40,0.85)', borderRadius: 18}} onSubmit={e => { e.preventDefault(); handleAsk(); }}>
                    <input
                        className="flex-1 bg-transparent outline-none text-base px-4 py-2"
                        style={{
                            color: '#fff',
                            boxShadow: 'none',
                            paddingTop: '10px',
                            paddingBottom: '10px',
                            lineHeight: '1.5',
                            minHeight: '40px',
                            overflow: 'hidden',
                            '::placeholder': {color: '#b0b6c3'}
                        }}
                        placeholder="Type your question..."
                        value={question}
                        rows={1}
                        onInput={e => {
                            const target = e.target as HTMLTextAreaElement;
                            target.style.height = '40px'; // reset to min height
                            target.style.height = target.scrollHeight + 'px';
                        }}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleAsk(); } }}
                    />
                    <button
                        type="submit"
                        disabled={loading || !question.trim()}
                        className="ml-2 flex items-center justify-center w-10 h-10"
                        style={{background: 'linear-gradient(90deg, #2563eb 0%, #1e40af 100%)', color: '#fff', borderRadius: '50%'}}
                        aria-label="Ask"
                    >
                        <Send className="w-5 h-5" />
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

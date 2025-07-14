import React, { useState, useEffect, useRef } from "react";
import Modal from "./UI/Modal";
import Button from "./UI/Button";
import Spinner from "./UI/Spinner";
import { Lightbulb, User, Bot, Send } from "lucide-react";
import ConsoleLog, { LogEntry } from "./ConsoleLog";
import { streamAiAnswer } from "../utils/streamAi";
import { getMistralChatHistory, addMistralChatHistory } from "../api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import useClickOutside from "../utils/useClickOutside";

interface Props {
    onClose: () => void;
    btnRect?: DOMRect | null;
    pageContext?: any;
}

interface ChatHistory {
    id: number;
    question: string;
    answer: string;
    created_at: string;
}

export default function AskAiModal({ onClose, btnRect, pageContext }: Props) {
    const [question, setQuestion] = useState("");
    const [markdown, setMarkdown] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [history, setHistory] = useState<ChatHistory[]>([]);
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const chatEndRef = useRef<HTMLDivElement>(null);
    const fullAnswerRef = useRef("");
    const [isStreaming, setIsStreaming] = useState(false);
    const modalRef = useRef<HTMLDivElement>(null);
    useClickOutside(modalRef, onClose);
    const [bufferedMarkdown, setBufferedMarkdown] = useState("");
    const [displayedMarkdown, setDisplayedMarkdown] = useState("");

    const addLog = (text: string) => {
        setLogs((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.text === text) {
                return [...prev.slice(0, -1), { ...last, count: last.count + 1 }];
            }
            return [...prev, { text, count: 1 }];
        });
    };

    // Prevent background scroll when modal is open
    useEffect(() => {
        document.body.classList.add('modal-open');
        return () => { document.body.classList.remove('modal-open'); };
    }, []);

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

    // Scroll to bottom as the AI streams new content
    useEffect(() => {
        if (isStreaming && chatEndRef.current) {
            chatEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [markdown]);

    // Scroll to bottom when history is loaded (on open)
    useEffect(() => {
      if (history.length > 0 && chatEndRef.current) {
        chatEndRef.current.scrollIntoView({ behavior: "auto" });
      }
    }, [history.length]);

    // Helper to check if markdown ends with an incomplete table or code block
    function isMarkdownBlockComplete(md: string) {
        // Check for code block
        const codeBlocks = (md.match(/```/g) || []).length;
        if (codeBlocks % 2 !== 0) return false; // Odd number of code block markers
        // Check for table: if last non-empty line starts with | or contains table header, wait for blank line
        const lines = md.split(/\r?\n/);
        let inTable = false;
        let inList = false;
        for (let i = lines.length - 1; i >= 0; i--) {
            const line = lines[i].trim();
            if (line === "") break;
            if (line.startsWith("|") ) { inTable = true; continue; }
            if (inTable && !line.startsWith("|")) return false;

            if (/^(\*|-|\+)\s+/.test(line) || /^\d+[.)]\s+/.test(line)) { inList = true; continue; }
            if (inList && !(/^(\*|-|\+)\s+/.test(line) || /^\d+[.)]\s+/.test(line))) return false;
        }
        return true;
    }

    // Helper to clean up markdown tables
    function fixMarkdownTables(md: string) {
        // Find all table blocks and clean them up
        return md.replace(/((?:^|\n)(?:\|[^\n]*\|\s*\n)+)/g, (tableBlock) => {
            // Remove extra spaces around pipes and ensure separator row is present
            const lines = tableBlock.trim().split(/\r?\n/).map(line => line.trim());
            if (lines.length < 2) return tableBlock; // Not a table
            // Ensure header separator row exists
            if (!/^\|?\s*-+\s*(\|\s*-+\s*)+\|?$/.test(lines[1])) {
                // Insert a separator row after the header
                const colCount = lines[0].split('|').length - 2;
                const sep = '|' + Array(colCount).fill(' --- ').join('|') + '|';
                lines.splice(1, 0, sep);
            }
            // Clean up each line
            return lines.map(line =>
                '|' + line.split('|').slice(1, -1).map(cell => cell.trim()).join(' | ') + '|'
            ).join('\n') + '\n';
        });
    }

    // Helper to strip outer code fences (``` and language label)
    function stripOuterCodeFences(md: string) {
        // Remove leading/trailing whitespace
        let text = md.trim();
        // Match triple backtick block with optional language
        const codeBlockRegex = /^```[a-zA-Z0-9]*\n([\s\S]*?)\n```$/;
        const match = text.match(codeBlockRegex);
        if (match) {
            text = match[1].trim();
        }
        // Remove leading 'markdown', 'text', or similar label (with optional colon or newline)
        text = text.replace(/^(markdown|text|md)[:\s-]*\n?/i, '');
        return text;
    }

    const handleAsk = async () => {
        if (!question.trim()) {
            setError("Please enter a question.");
            return;
        }

        try {
            setLoading(true);
            setIsStreaming(true);
            addLog("[info] Streaming request sent");
            setMarkdown("");
            setBufferedMarkdown("");
            setDisplayedMarkdown("");
            fullAnswerRef.current = "";

            await streamAiAnswer(question.trim(), (chunk) => {
                fullAnswerRef.current = chunk.text;
                let cleaned = stripOuterCodeFences(chunk.text);
                cleaned = fixMarkdownTables(cleaned);
                setBufferedMarkdown(cleaned);
                if (isMarkdownBlockComplete(cleaned)) {
                    setDisplayedMarkdown(cleaned);
                }
                addLog(`[debug] chunk: ${cleaned.slice(-40)}`);
            }, pageContext);

            setIsStreaming(false);

            // After streaming, if no answer, show placeholder
            if (!fullAnswerRef.current.trim()) {
                setMarkdown("[No answer returned by AI]");
                setDisplayedMarkdown("[No answer returned by AI]");
            } else {
                setMarkdown(fullAnswerRef.current);
                setDisplayedMarkdown(fullAnswerRef.current);
                console.log("[DEBUG] Full AI answer after streaming:", fullAnswerRef.current);
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
            addLog("[error] stream failed");
            setError("Failed to get answer.");
        } finally {
            addLog("[info] streaming finished");
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
        boxShadow: "0 8px 32px rgba(0,0,0,0.22)",
        background: "#000",
        color: "#fff",
        backdropFilter: "blur(22px)",
        WebkitBackdropFilter: "blur(22px)",
        borderRadius: 28,
        padding: 0,
        maxHeight: "80vh",
        display: "flex",
        flexDirection: "column",
    };
    let arrowStyle: React.CSSProperties = {};
    if (btnRect) {
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
            <div ref={modalRef} style={modalStyle} className="z-50 animate-fade-in rounded-2xl overflow-visible border border-white/30 shadow-xl relative speech-bubble-modal">
              <div className="relative text-white flex flex-col" style={{overflow: 'hidden'}}>
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
                <div className="flex-1 overflow-y-auto px-3 sm:px-4 py-3 space-y-2 sm:space-y-3 max-h-64 min-h-[120px]" style={{background: "rgba(255,255,255,0.04)"}}>
                    {history.length === 0 && markdown === "" && (
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
                                            className="rounded-2xl px-3 sm:px-4 py-2 shadow text-sm relative chat-bubble-ai min-h-[36px] w-full bg-black text-white"
                                            style={{
                                                backdropFilter: 'blur(12px)',
                                                WebkitBackdropFilter: 'blur(12px)',
                                                background: 'rgba(0,0,0,0.6)',
                                                border: '1.5px solid #1e3a8a',
                                                boxShadow: '0 2px 16px 0 rgba(80,120,200,0.10)',
                                                fontSize: '0.97rem',
                                                fontFamily: 'Inter, Segoe UI, system-ui, sans-serif',
                                                color: '#fff',
                                                lineHeight: 1.5,
                                                wordBreak: 'break-word',
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
                                            <span className="absolute left-[-10px] bottom-0 w-0 h-0" style={{
                                                borderTop: '12px solid rgba(255,255,255,0.18)',
                                                borderRight: '12px solid transparent',
                                                borderBottom: 0,
                                                borderLeft: 0,
                                            }} />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </React.Fragment>
                    ))}
                    {/* Render current question/answer if present */}
                    {markdown !== "" && (
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
                            {/* AI bubble (single, live-updating) */}
                            <div className="flex items-end gap-1 sm:gap-2 justify-start w-full">
                                <div className="flex items-end gap-1 sm:gap-2 w-full justify-start">
                                    <div className="rounded-full bg-blue-900 w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center text-white font-bold shadow"><Bot className="w-4 h-4 sm:w-5 sm:h-5" /></div>
                                    <div className="relative w-full" style={{maxWidth: 480, margin: '0 auto'}}>
                                        <div
                                            className="bg-black text-white rounded-2xl px-3 sm:px-4 py-2 shadow text-sm relative chat-bubble-ai min-h-[36px] w-full"
                                            style={{
                                                backdropFilter: 'blur(6px)',
                                                WebkitBackdropFilter: 'blur(6px)',
                                                background: 'rgba(0,0,0,0.75)',
                                                border: '1.5px solid #1e3a8a',
                                                boxShadow: '0 2px 12px 0 rgba(80,120,200,0.07)',
                                                fontSize: '0.95rem',
                                                fontFamily: 'Inter, Segoe UI, system-ui, sans-serif',
                                                color: '#fff',
                                                lineHeight: 1.5,
                                                wordBreak: 'break-word',
                                                whiteSpace: undefined,
                                                margin: '6px 0 10px 0',
                                                padding: '14px 16px',
                                                borderRadius: '20px',
                                                maxWidth: '100%',
                                            }}
                                        >
                                            <ReactMarkdown
                                                key={displayedMarkdown}
                                                remarkPlugins={[remarkGfm]}
                                                children={displayedMarkdown}
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
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>
                <ConsoleLog logs={logs} />
                {/* Input area */}
                <form className="flex items-center gap-2 px-3 sm:px-4 py-3 border-t border-white/30 bg-transparent" onSubmit={e => { e.preventDefault(); handleAsk(); }}>
                    <div className="flex-1 flex items-center bg-black rounded-full shadow border border-blue-800 px-3 py-1" style={{backdropFilter: 'blur(8px)'}}>
                        <textarea
                            className="flex-1 h-10 sm:h-11 max-h-20 min-h-[40px] sm:min-h-[44px] bg-transparent text-white resize-none focus:ring-0 focus:outline-none placeholder-gray-500 border-0 p-0 m-0 align-middle text-sm sm:text-base"
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
                {/* Speech bubble tail (SVG) */}
                {btnRect && (
                  <svg style={arrowStyle} viewBox="0 0 48 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M0 0 Q24 32 48 0" fill="rgba(255,255,255,0.10)" filter="url(#shadow)" />
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

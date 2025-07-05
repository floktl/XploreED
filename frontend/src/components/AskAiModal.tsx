import React, { useState } from "react";
import Modal from "./UI/Modal";
import Button from "./UI/Button";
import Spinner from "./UI/Spinner";
import { streamAiAnswer } from "../utils/streamAi";

interface Props {
  onClose: () => void;
}

interface AnswerBlock {
  type: string;
  text: string;
}

export default function AskAiModal({ onClose }: Props) {
  const [question, setQuestion] = useState("");
  const [answerBlocks, setAnswerBlocks] = useState<AnswerBlock[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }
    try {
      setLoading(true);
      setAnswerBlocks([]);
      await streamAiAnswer(question.trim(), (chunk) => {
        setAnswerBlocks((prev) => [...prev, chunk]);
      });
      setError("");
    } catch (err) {
      console.error("❌ AI streaming error:", err);
      setError("Failed to get answer.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal onClose={onClose}>
      <h2 className="text-lg font-bold mb-2">Ask AI</h2>
      <textarea
        className="w-full h-28 p-2 rounded border dark:bg-gray-800 dark:text-white mb-3"
        placeholder="Ask a question in English or German..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
      {loading && (
        <div className="flex items-center gap-2 mb-2">
          <Spinner /> <span className="italic">AI thinking...</span>
        </div>
      )}
      {answerBlocks.length > 0 && (
        <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded mb-2 space-y-2">
          {answerBlocks.map((block, idx) => (
            block.type === "heading" ? (
              <h3 key={idx} className="text-xl font-bold mt-4">{block.text}</h3>
            ) : block.type === "tip" ? (
              <div key={idx} className="bg-yellow-100 border-l-4 border-yellow-500 p-2 text-sm italic">
                💡 {block.text}
              </div>
            ) : block.type === "quote" ? (
              <blockquote key={idx} className="border-l-4 border-blue-400 pl-3 italic text-gray-600">
                “{block.text}”
              </blockquote>
            ) : (
              <p key={idx} className="whitespace-pre-wrap">{block.text}</p>
            )
          ))}
        </div>
      )}
      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>Close</Button>
        <Button variant="primary" onClick={handleAsk} disabled={loading}>Ask</Button>
      </div>
    </Modal>
  );
}

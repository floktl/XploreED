import React, { useState } from "react";
import Modal from "./UI/Modal";
import Button from "./UI/Button";
import Spinner from "./UI/Spinner";
import { askAiQuestion } from "../api";
import { streamAiAnswer } from "../utils/streamAi";

interface Props {
  onClose: () => void;
}

export default function AskAiModal({ onClose }: Props) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }
    try {
      setLoading(true);
      setAnswer("");
      await streamAiAnswer(question.trim(), (chunk) => {
        setAnswer((prev) => prev + chunk);
      });
      setError("");
    } catch (err) {
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
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
      {loading && (
        <div className="flex items-center gap-2 mb-2">
          <Spinner /> <span className="italic">AI thinking...</span>
        </div>
      )}
      {answer && (
        <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded mb-2 whitespace-pre-wrap">
          {answer}
        </div>
      )}
      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>Close</Button>
        <Button variant="primary" onClick={handleAsk} disabled={loading}>Ask</Button>
      </div>
    </Modal>
  );
}

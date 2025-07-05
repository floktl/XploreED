import React, { useState } from "react";
import Modal from "./UI/Modal";
import Button from "./UI/Button";

interface Props {
  exercise: { id: number | string; question: string };
  userAnswer: string;
  correctAnswer: string;
  onSend: (message: string) => Promise<void>;
  onClose: () => void;
}

export default function ReportExerciseModal({
  exercise,
  userAnswer,
  correctAnswer,
  onSend,
  onClose,
}: Props) {
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (!msg.trim()) {
      setError("Please describe the issue.");
      return;
    }
    try {
      setSending(true);
      await onSend(msg.trim());
      setSuccess(true);
      setError("");
    } catch (err) {
      setError("Failed to send report.");
    } finally {
      setSending(false);
    }
  };

  return (
    <Modal onClose={onClose}>
      <h2 className="text-lg font-bold mb-2">Report Exercise Error</h2>
      <p className="mb-2 text-sm break-words">
        <strong>Question:</strong> {exercise.question}
      </p>
      <p className="mb-1 text-sm break-words">
        <strong>Your answer:</strong> {userAnswer || "(empty)"}
      </p>
      <p className="mb-2 text-sm break-words">
        <strong>AI answer:</strong> {correctAnswer}
      </p>
      <textarea
        className="w-full h-32 p-2 rounded border dark:bg-gray-800 dark:text-white mb-3"
        value={msg}
        onChange={(e) => setMsg(e.target.value)}
      />
      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
      {success && (
        <p className="text-green-600 text-sm mb-2">Thank you for reporting!</p>
      )}
      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button variant="primary" onClick={handleSend} disabled={sending}>
          Send
        </Button>
      </div>
    </Modal>
  );
}

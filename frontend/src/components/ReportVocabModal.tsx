import React, { useState } from "react";
import Modal from "./UI/Modal";
import Button from "./UI/Button";

interface Props {
  vocab: {
    id: number;
    vocab: string;
    translation: string;
    article?: string | null;
    word_type?: string | null;
  };
  onSend: (message: string) => Promise<void>;
  onClose: () => void;
}

export default function ReportVocabModal({ vocab, onSend, onClose }: Props) {
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
    } catch {
      setError("Failed to send report.");
    } finally {
      setSending(false);
    }
  };

  return (
    <Modal onClose={onClose}>
      <h2 className="text-lg font-bold mb-2">Report Vocabulary Error</h2>
      <p className="mb-2 text-sm break-words">
        <strong>Word:</strong>{" "}
        {vocab.article ? `${vocab.article} ${vocab.vocab}` : vocab.vocab}
      </p>
      <p className="mb-2 text-sm break-words">
        <strong>Translation:</strong> {vocab.translation}
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
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button variant="primary" onClick={handleSend} disabled={sending}>
          Send
        </Button>
      </div>
    </Modal>
  );
}

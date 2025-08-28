import React, { useState } from "react";
import Button from "../../../../common/UI/Button";

interface ReportFormProps {
    onSend: (message: string) => Promise<void>;
    onCancel: () => void;
}

export default function ReportForm({ onSend, onCancel }: ReportFormProps) {
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
        <div>
            <textarea
                className="w-full h-32 p-2 rounded border dark:bg-gray-800 dark:text-white mb-3"
                value={msg}
                onChange={(e) => setMsg(e.target.value)}
                placeholder="Describe the issue with this vocabulary..."
            />
            {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
            {success && (
                <p className="text-green-600 text-sm mb-2">Thank you for reporting!</p>
            )}
            <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={onCancel}>
                    Cancel
                </Button>
                <Button variant="primary" onClick={handleSend} disabled={sending}>
                    Send
                </Button>
            </div>
        </div>
    );
}

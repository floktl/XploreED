import React, { useState } from "react";
import { Container, Title, Input } from "./UI/UI";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";
import { sendSupportFeedback } from "../api";

export default function Support() {
  const darkMode = useAppStore((s) => s.darkMode);
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setStatus("");
    const trimmed = message.trim();
    if (!trimmed) {
      setError("Please enter a message.");
      return;
    }
    try {
      setIsSubmitting(true);
      const res = await sendSupportFeedback(trimmed);
      if (res && !res.error) {
        setStatus("Thanks! Your message was sent.");
        setMessage("");
      } else {
        setError(res?.error || "Failed to send feedback");
      }
    } catch (_) {
      setError("Failed to send feedback");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>Support</Title>
        <Card>
          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block text-sm font-medium mb-1">How can we help?</label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className={`w-full h-32 p-3 rounded border ${darkMode ? "bg-gray-800 border-gray-700" : "bg-white border-gray-300"}`}
              placeholder="Describe your issue or share feedback..."
            />
            {error && <Alert type="danger">{error}</Alert>}
            {status && <Alert type="success">{status}</Alert>}
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? "Sending..." : "Send"}
            </Button>
          </form>
        </Card>
      </Container>
      <Footer />
    </div>
  );
}


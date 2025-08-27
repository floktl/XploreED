import React from "react";
import Card from "../UI/Card";
import Button from "../UI/Button";
import Alert from "../UI/Alert";

export default function SupportForm({
  message,
  setMessage,
  error,
  status,
  isSubmitting,
  onSubmit,
  darkMode
}) {
  return (
    <Card>
      <form onSubmit={onSubmit} className="space-y-4">
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
  );
}

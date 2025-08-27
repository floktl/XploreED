import React from "react";
import Modal from "../UI/Modal";
import Button from "../UI/Button";
import Alert from "../UI/Alert";

export default function TopicMemoryClearModal({
  showClear,
  onClose,
  onClear,
  error
}) {
  if (!showClear) return null;

  return (
    <Modal onClose={onClose}>
      <h2 className="text-lg font-bold mb-2">Delete Topic Memory</h2>
      <p className="mb-4">Are you sure you want to delete all saved topic memory?</p>
      {error && <Alert type="error" className="mb-2">{error}</Alert>}
      <div className="flex justify-end gap-2">
        <Button variant="danger" onClick={onClear}>Delete</Button>
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </Modal>
  );
}

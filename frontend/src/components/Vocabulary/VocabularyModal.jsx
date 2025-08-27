import React from "react";
import Modal from "../UI/Modal";
import Button from "../UI/Button";

export default function VocabularyModal({
  selected,
  onClose,
  onForget,
  onShowReport
}) {
  if (!selected) return null;

  return (
    <Modal onClose={onClose}>
      <h2 className="text-xl font-semibold mb-4">
        {selected.article ? `${selected.article} ${selected.vocab}` : selected.vocab}
      </h2>
      <p className="mb-2"><strong>Translation:</strong> {selected.translation}</p>
      {selected.details && (<p className="mb-2"><strong>Info:</strong> {selected.details}</p>)}
      {selected.word_type && (<p className="mb-2 capitalize"><strong>Type:</strong> {selected.word_type}</p>)}
      {selected.created_at && (<p className="mb-2"><strong>Learned:</strong> {new Date(selected.created_at).toLocaleString()}</p>)}
      {selected.next_review && (<p className="mb-2"><strong>Next review:</strong> {new Date(selected.next_review).toLocaleDateString()}</p>)}
      {selected.context && (<p className="mb-2"><strong>Context:</strong> {selected.context}</p>)}
      {selected.exercise && (<p className="mb-2"><strong>Exercise:</strong> {selected.exercise}</p>)}
      <div className="flex justify-end gap-2 mt-4">
        <Button variant="danger" onClick={() => onForget(selected)}>Forget</Button>
        <Button variant="secondary" onClick={onShowReport}>Report</Button>
      </div>
    </Modal>
  );
}

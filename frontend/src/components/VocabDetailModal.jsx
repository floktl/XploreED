import React from "react";
import Modal from "./UI/Modal";

export default function VocabDetailModal({ vocab, onClose }) {
    if (!vocab) return null;
    return (
        <Modal onClose={onClose}>
            <h2 className="text-xl font-semibold mb-4">
                {vocab.article ? `${vocab.article} ${vocab.vocab}` : vocab.vocab}
            </h2>
            <p className="mb-2"><strong>Translation:</strong> {vocab.translation}</p>
            {vocab.details && (<p className="mb-2"><strong>Info:</strong> {vocab.details}</p>)}
            {vocab.word_type && (<p className="mb-2 capitalize"><strong>Type:</strong> {vocab.word_type}</p>)}
            {vocab.created_at && (<p className="mb-2"><strong>Learned:</strong> {new Date(vocab.created_at).toLocaleString()}</p>)}
            {vocab.next_review && (<p className="mb-2"><strong>Next review:</strong> {new Date(vocab.next_review).toLocaleDateString()}</p>)}
            {vocab.context && (<p className="mb-2"><strong>Context:</strong> {vocab.context}</p>)}
            {vocab.exercise && (<p className="mb-2"><strong>Exercise:</strong> {vocab.exercise}</p>)}
        </Modal>
    );
}

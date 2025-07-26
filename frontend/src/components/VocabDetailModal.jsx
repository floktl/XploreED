import React from "react";
import Modal from "./UI/Modal";

export default function VocabDetailModal({ vocab, onClose, title = "Vocabulary Details" }) {
    if (!vocab) return null;

    const formatDate = (dateString) => {
        if (!dateString) return null;
        const date = new Date(dateString);
        return date.toLocaleDateString('en-GB') + ', ' + date.toLocaleTimeString('en-GB', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    const formatReviewDate = (dateString) => {
        if (!dateString) return null;
        const date = new Date(dateString);
        return date.toLocaleDateString('en-GB');
    };

    return (
        <Modal onClose={onClose}>
            <div className="text-left">
                <h2 className="text-xl font-bold mb-4 text-white">
                    {title}
                </h2>

                <div className="space-y-2 text-sm">
                    <p><span className="text-gray-300">Word:</span> <span className="font-semibold text-white">{vocab.article ? `${vocab.article} ${vocab.vocab}` : vocab.vocab}</span></p>

                    <p><span className="text-gray-300">Translation:</span> <span className="font-semibold text-white">{vocab.translation}</span></p>

                    {vocab.details && (
                        <p><span className="text-gray-300">Info:</span> <span className="text-gray-200">{vocab.details}</span></p>
                    )}

                    {vocab.word_type && (
                        <p><span className="text-gray-300">Type:</span> <span className="font-semibold text-white capitalize">{vocab.word_type}</span></p>
                    )}

                    {vocab.created_at && (
                        <p><span className="text-gray-300">Learned:</span> <span className="font-semibold text-white">{formatDate(vocab.created_at)}</span></p>
                    )}

                    {vocab.next_review && (
                        <p><span className="text-gray-300">Next review:</span> <span className="font-semibold text-white">{formatReviewDate(vocab.next_review)}</span></p>
                    )}

                    {vocab.exercise && (
                        <p><span className="text-gray-300">Exercise:</span> <span className="font-semibold text-white">{vocab.exercise}</span></p>
                    )}
                </div>

                <div className="flex justify-end mt-6">
                    <button
                        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                        onClick={onClose}
                    >
                        Close
                    </button>
                </div>
            </div>
        </Modal>
    );
}

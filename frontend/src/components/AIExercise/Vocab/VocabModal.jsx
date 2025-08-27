import React from "react";
import Modal from "../../UI/Modal";
import Spinner from "../../UI/Spinner";
import VocabDetailModal from "../../VocabDetailModal";

export default function VocabModal({
    vocabLoading,
    setVocabLoading,
    vocabModal,
    setVocabModal,
    isNewVocab
}) {
    return (
        <>
            {vocabLoading && (
                <Modal onClose={() => setVocabLoading(false)}>
                    <div className="flex justify-center items-center py-8">
                        <Spinner />
                        <span className="ml-4 text-lg">Loading vocabulary...</span>
                    </div>
                </Modal>
            )}
            {vocabModal && (
                <VocabDetailModal
                    vocab={vocabModal}
                    onClose={() => setVocabModal(null)}
                    title={isNewVocab ? "New Vocab Learned" : "Vocabulary Details"}
                />
            )}
        </>
    );
}

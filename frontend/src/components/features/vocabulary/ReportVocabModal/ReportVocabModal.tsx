import React from "react";
import Modal from "../../../common/UI/Modal";
import VocabDetails from "./Components/VocabDetails";
import ReportForm from "./Forms/ReportForm";

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
    return (
        <Modal onClose={onClose}>
            <h2 className="text-lg font-bold mb-2">Report Vocabulary Error</h2>

            <VocabDetails vocab={vocab} />

            <ReportForm
                onSend={onSend}
                onCancel={onClose}
            />
        </Modal>
    );
}

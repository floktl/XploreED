import Modal from "../../../common/UI/Modal";
import VocabDetails from "./Components/VocabDetails";

export default function VocabDetailModal({ vocab, onClose, title = "Vocabulary Details" }) {
    if (!vocab) return null;

    return (
        <Modal onClose={onClose}>
            <div className="text-left">
                <h2 className="text-xl font-bold mb-4 text-white">
                    {title}
                </h2>

                <VocabDetails vocab={vocab} />

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

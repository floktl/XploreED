import { formatDate, formatReviewDate } from "../Utils/dateUtils";

export default function VocabDetails({ vocab }) {
    if (!vocab) return null;

    return (
        <div className="space-y-2 text-sm">
            <p>
                <span className="text-gray-300">Word:</span>{" "}
                <span className="font-semibold text-white">
                    {vocab.article ? `${vocab.article} ${vocab.vocab}` : vocab.vocab}
                </span>
            </p>

            <p>
                <span className="text-gray-300">Translation:</span>{" "}
                <span className="font-semibold text-white">{vocab.translation}</span>
            </p>

            {vocab.details && (
                <p>
                    <span className="text-gray-300">Info:</span>{" "}
                    <span className="text-gray-200">{vocab.details}</span>
                </p>
            )}

            {vocab.word_type && (
                <p>
                    <span className="text-gray-300">Type:</span>{" "}
                    <span className="font-semibold text-white capitalize">{vocab.word_type}</span>
                </p>
            )}

            {vocab.created_at && (
                <p>
                    <span className="text-gray-300">Learned:</span>{" "}
                    <span className="font-semibold text-white">{formatDate(vocab.created_at)}</span>
                </p>
            )}

            {vocab.next_review && (
                <p>
                    <span className="text-gray-300">Next review:</span>{" "}
                    <span className="font-semibold text-white">{formatReviewDate(vocab.next_review)}</span>
                </p>
            )}

            {vocab.exercise && (
                <p>
                    <span className="text-gray-300">Exercise:</span>{" "}
                    <span className="font-semibold text-white">{vocab.exercise}</span>
                </p>
            )}
        </div>
    );
}

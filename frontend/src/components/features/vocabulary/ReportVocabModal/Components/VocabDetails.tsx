import React from "react";

interface VocabDetailsProps {
    vocab: {
        id: number;
        vocab: string;
        translation: string;
        article?: string | null;
        word_type?: string | null;
    };
}

export default function VocabDetails({ vocab }: VocabDetailsProps) {
    return (
        <div className="mb-2">
            <p className="mb-2 text-sm break-words">
                <strong>Word:</strong>{" "}
                {vocab.article ? `${vocab.article} ${vocab.vocab}` : vocab.vocab}
            </p>
            <p className="mb-2 text-sm break-words">
                <strong>Translation:</strong> {vocab.translation}
            </p>
        </div>
    );
}

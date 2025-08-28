import diffWords from "../../../../../utils/diffWords";

export default function FeedbackSummary({ summary }) {
    if (!summary) return null;

    return (
        <div>
            <p className="font-medium mb-2">
                You answered {summary.correct} of {summary.total} questions correctly.
            </p>
            {summary.mistakes && summary.mistakes.length > 0 && (
                <div className="text-sm">
                    <p className="font-semibold">Mistakes</p>
                    <ul className="list-disc pl-5 space-y-1">
                        {summary.mistakes.map((m, i) => (
                            <li key={i}>
                                <span className="font-medium">{m.question}</span> – {diffWords(m.your_answer, m.correct_answer)}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

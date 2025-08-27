import React from "react";
import Card from "../UI/Card";
import Button from "../UI/Button";
import Spinner from "../UI/Spinner";
import FeedbackBlock from "../FeedbackBlock";

export default function AIReadingContent({
  data,
  answers,
  results,
  submitted,
  feedbackBlocks,
  onSelect,
  loading
}) {
  return (
    <Card className="space-y-4">
      {data.text.split(/\n\n+/).map((para, idx) => (
        <p key={idx} className="mb-3 whitespace-pre-line">{para}</p>
      ))}
      {data.questions.map((q, idx) => (
        <div key={q.id} className="space-y-2">
          <p className="font-medium">{q.question}</p>
          {q.options.map((opt) => {
            const isCorrect = results[q.id] === opt;
            const isSelected = answers[q.id] === opt;
            let variant = "secondary";
            if (!submitted) {
              variant = isSelected ? "primary" : "secondary";
            } else {
              if (isCorrect) variant = "successBright";
              else if (isSelected) variant = "danger";
            }
            return (
              <Button key={opt} type="button" variant={variant} onClick={() => onSelect(q.id, opt)} disabled={submitted}>
                {opt}
              </Button>
            );
          })}
          {submitted && (feedbackBlocks && feedbackBlocks[idx]) && (
            <div className="mt-2">
              <FeedbackBlock {...feedbackBlocks[idx]} />
            </div>
          )}
        </div>
      ))}
      {submitted && data.feedbackPrompt && (
        <Card className="bg-blue-50 dark:bg-blue-900 text-blue-900 dark:text-blue-100 p-4 mt-6">
          <div className="font-semibold mb-2">AI Feedback</div>
          <div>{data.feedbackPrompt}</div>
        </Card>
      )}
      {submitted && loading && (
        <div className="flex flex-col items-center gap-2">
          <Spinner />
          <p>AI is thinking...</p>
        </div>
      )}
    </Card>
  );
}

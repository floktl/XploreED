import React from "react";
import Card from "../UI/Card";
import Button from "../UI/Button";
import FeedbackBlock from "../FeedbackBlock";

export default function TranslationFeedback({ feedbackBlock, onReset }) {
  if (!feedbackBlock) return null;

  return (
    <>
      <Card className="mt-8 max-w-2xl mx-auto">
        <FeedbackBlock
          status={feedbackBlock.status}
          correct={feedbackBlock.correct}
          alternatives={feedbackBlock.alternatives}
          explanation={feedbackBlock.explanation}
          userAnswer={feedbackBlock.userAnswer}
          diff={feedbackBlock.diff}
        />
      </Card>

      <div className="mt-6 text-center">
        <Button variant="secondary" onClick={onReset}>
          🆕 New Translation
        </Button>
      </div>
    </>
  );
}

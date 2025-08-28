import Alert from "../../../common/UI/Alert";

export default function LevelGameFeedback({ feedback }) {
  if (!feedback) return null;

  return (
    <div className="mt-6 max-w-xl mx-auto feedback-fade-in">
      <strong>Feedback:</strong>
      <Alert type={feedback.correct ? "success" : "error"} className="mt-1">
        <div
          className="text-sm"
          dangerouslySetInnerHTML={{
            __html: feedback.feedback || "No feedback",
          }}
        />
      </Alert>
    </div>
  );
}

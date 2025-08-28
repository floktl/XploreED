import { AlertCircle, CheckCircle, Info, BookOpen } from "lucide-react";
import { parseFeedback } from "./Utils/feedbackParser";
import FeedbackSection from "./Components/FeedbackSection";

export default function PrettyFeedback({ feedback }) {
  if (!feedback) return null;
  const sections = parseFeedback(feedback);

  return (
    <div className="space-y-4">
      <FeedbackSection
        icon={BookOpen}
        title="Translation"
        content={sections.translation}
        colorClass="text-blue-700"
      />

      <FeedbackSection
        icon={CheckCircle}
        title="Evaluation"
        content={sections.evaluation}
        colorClass="text-green-700"
      />

      <FeedbackSection
        icon={Info}
        title="Additional Notes"
        content={sections.notes}
        colorClass="text-yellow-700"
      />

      <FeedbackSection
        icon={AlertCircle}
        title="Example"
        content={sections.example}
        colorClass="text-purple-700"
      />
    </div>
  );
}

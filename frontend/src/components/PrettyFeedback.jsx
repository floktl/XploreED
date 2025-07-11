import React from "react";
import ReactMarkdown from "react-markdown";
import { AlertCircle, CheckCircle, Info, BookOpen } from "lucide-react";

function parseFeedback(feedback) {
  // Simple regex-based section splitting
  const sections = {};
  const translationMatch = feedback.match(/\*\*Translation:\*\*([\s\S]*?)(\*\*|$)/);
  const evaluationMatch = feedback.match(/\*\*Evaluation:\*\*([\s\S]*?)(\*\*|$)/);
  const notesMatch = feedback.match(/\*\*Additional Notes:\*\*([\s\S]*?)(\*\*|$)/);
  const exampleMatch = feedback.match(/Here\'s an example[\s\S]*$/);

  if (translationMatch) sections.translation = translationMatch[1].trim();
  if (evaluationMatch) sections.evaluation = evaluationMatch[1].trim();
  if (notesMatch) sections.notes = notesMatch[1].trim();
  if (exampleMatch) sections.example = exampleMatch[0].trim();

  return sections;
}

export default function PrettyFeedback({ feedback }) {
  if (!feedback) return null;
  const sections = parseFeedback(feedback);

  return (
    <div className="space-y-4">
      {sections.translation && (
        <div className="flex items-center gap-2 text-blue-700 font-semibold">
          <BookOpen className="w-5 h-5" />
          <span>Translation</span>
        </div>
      )}
      {sections.translation && (
        <ReactMarkdown className="pl-6">{sections.translation}</ReactMarkdown>
      )}

      {sections.evaluation && (
        <div className="flex items-center gap-2 text-green-700 font-semibold">
          <CheckCircle className="w-5 h-5" />
          <span>Evaluation</span>
        </div>
      )}
      {sections.evaluation && (
        <ReactMarkdown className="pl-6">{sections.evaluation}</ReactMarkdown>
      )}

      {sections.notes && (
        <div className="flex items-center gap-2 text-yellow-700 font-semibold">
          <Info className="w-5 h-5" />
          <span>Additional Notes</span>
        </div>
      )}
      {sections.notes && (
        <ReactMarkdown className="pl-6">{sections.notes}</ReactMarkdown>
      )}

      {sections.example && (
        <div className="flex items-center gap-2 text-purple-700 font-semibold">
          <AlertCircle className="w-5 h-5" />
          <span>Example</span>
        </div>
      )}
      {sections.example && (
        <ReactMarkdown className="pl-6">{sections.example}</ReactMarkdown>
      )}
    </div>
  );
}

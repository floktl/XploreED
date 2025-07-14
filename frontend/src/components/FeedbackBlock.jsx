import React from "react";
import { CheckCircle, XCircle } from "lucide-react";

export default function FeedbackBlock({
  status,
  correct,
  alternatives = [],
  explanation,
  userAnswer,
  diff,
  children,
}) {
  return (
    <div className="p-4 rounded bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-100 space-y-2">
      <div className="flex items-center gap-2 font-bold">
        {status === "correct" ? (
          <span className="text-green-700 dark:text-green-400 flex items-center gap-1">
            <CheckCircle className="w-5 h-5" /> Correct!
          </span>
        ) : (
          <span className="text-red-700 dark:text-red-400 flex items-center gap-1">
            <XCircle className="w-5 h-5" /> Incorrect.
          </span>
        )}
      </div>
      <div>
        <strong className="text-green-700 dark:text-green-400">Correct answer:</strong>
        <span className="font-mono ml-2">{correct}</span>
      </div>
      <div>
        <strong className="text-blue-700 dark:text-blue-400">Alternative correct answers:</strong>
        {alternatives.length > 0 ? (
          <ul className="list-disc ml-6 mt-1">
            {alternatives.map((alt, i) => (
              <li key={i} className="font-mono">{alt}</li>
            ))}
          </ul>
        ) : (
          <span className="ml-2 text-gray-800 dark:text-gray-100">No alternative correct answers.</span>
        )}
      </div>
      <div>
        <strong className="text-gray-700 dark:text-gray-200">Explanation:</strong>
        <span className="ml-2 text-gray-800 dark:text-gray-100">
          {explanation || <span>No explanation available.</span>}
        </span>
      </div>
      {diff && (
        <div>
          <strong className="text-gray-700 dark:text-gray-200">Your answer vs. correct answer:</strong>
          <span className="ml-2 font-mono">{diff}</span>
        </div>
      )}
      {children}
    </div>
  );
}

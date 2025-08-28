import { diffWithNeutral, diffWithNeutralCorrect } from "../Utils/diffUtils";

export default function FeedbackDifference({ userAnswer, correct, status }) {
  if (status === 'correct' || typeof userAnswer === 'undefined' || typeof correct === 'undefined') {
    return null;
  }

  return (
    <div className="mt-2">
      <strong className="text-gray-700 dark:text-gray-200">Difference:</strong>
      <div className="flex flex-col gap-1 ml-2">
        <div>
          <span className="text-gray-500 text-xs">Your answer:</span>
          <div className="font-mono bg-gray-100 dark:bg-gray-800 rounded px-2 py-1 mt-1">
            {diffWithNeutral(userAnswer, correct)}
          </div>
        </div>
        <div>
          <span className="text-gray-500 text-xs">Correct answer:</span>
          <div className="font-mono bg-green-50 dark:bg-green-900 rounded px-2 py-1 mt-1">
            {diffWithNeutralCorrect(userAnswer, correct)}
          </div>
        </div>
      </div>
    </div>
  );
}

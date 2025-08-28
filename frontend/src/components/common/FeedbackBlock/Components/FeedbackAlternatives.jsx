import Spinner from "../../UI/Spinner";

export default function FeedbackAlternatives({ alternatives, loading }) {
  return (
    <div>
      <strong className="text-blue-700 dark:text-blue-400">Alternative correct answers:</strong>
      {loading ? (
        <div className="flex items-center gap-2 ml-2 mt-1">
          <Spinner size="sm" />
          <span className="text-gray-600 dark:text-gray-400 text-sm">Generating alternatives...</span>
        </div>
      ) : alternatives.length > 0 ? (
        <ul className="list-disc ml-6 mt-1">
          {alternatives.map((alt, i) => (
            <li key={i} className="font-mono">{alt}</li>
          ))}
        </ul>
      ) : (
        <span className="ml-2 text-gray-800 dark:text-gray-100">No alternative correct answers.</span>
      )}
    </div>
  );
}

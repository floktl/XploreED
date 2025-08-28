import Button from "../common/UI/Button";

const LessonProgress = ({ percentComplete, markedComplete, canComplete, onMarkComplete }) => {
  return (
    <div className="mb-6">
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Progress: {Math.round(percentComplete)}%
      </p>
      <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded">
        <div
          className="h-2 bg-green-500 rounded"
          style={{ width: `${percentComplete}%` }}
        ></div>
      </div>

      <div className="mt-4 text-right">
        <Button
          variant={markedComplete ? "secondary" : "success"}
          disabled={!canComplete || markedComplete}
          onClick={onMarkComplete}
        >
          {markedComplete ? "✅ Marked as Completed" : "✅ Mark Lesson as Completed"}
        </Button>
      </div>
    </div>
  );
};

export default LessonProgress;

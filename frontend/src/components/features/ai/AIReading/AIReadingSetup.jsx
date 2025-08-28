import Card from "../../../common/UI/Card";
import Button from "../../../common/UI/Button";
import ProgressRing from "../../../common/UI/ProgressRing";
import Spinner from "../../../common/UI/Spinner";

export default function AIReadingSetup({
  style,
  setStyle,
  onStartExercise,
  loading,
  progressPercentage,
  progressStatus,
  progressIcon
}) {
  return (
    <Card className="space-y-4">
      <label className="block font-medium">Choose a text type:</label>
      <select value={style} onChange={(e) => setStyle(e.target.value)} className="border p-2 rounded-md">
        <option value="story">Story</option>
        <option value="letter">Letter</option>
        <option value="news">News</option>
      </select>
      <Button onClick={onStartExercise} variant="primary">Start</Button>
      {loading && (
        <div className="text-center py-8">
          <div className="flex justify-center mb-6">
            <ProgressRing
              percentage={progressPercentage}
              size={120}
              color={progressPercentage === 100 ? "#10B981" : "#3B82F6"}
            />
          </div>
          <div className="flex items-center justify-center gap-3 mb-4">
            {React.createElement(progressIcon, { className: "w-6 h-6 text-blue-600 dark:text-blue-400" })}
            <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
              {progressStatus}
            </h3>
          </div>
          <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
            {progressPercentage < 100
              ? "We're crafting a personalized reading exercise for you."
              : "Your reading exercise is ready!"}
          </p>
          {progressPercentage < 100 && (
            <div className="mt-6 flex justify-center">
              <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                <Spinner />
                <span>Please wait...</span>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

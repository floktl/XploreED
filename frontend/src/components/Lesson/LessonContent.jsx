import Card from "../common/UI/Card";
import Button from "../common/UI/Button";
import BlockContentRenderer from "../common/BlockContentRenderer/BlockContentRenderer";
import AIExerciseBlock from "../features/ai/AIExercise/AIExerciseBlock";

const LessonContent = ({
  entries,
  progress,
  setActions,
  lessonId,
  showAi,
  setShowAi,
  updateLessonBlockProgress,
  refreshProgress,
  refreshCompletionStatus,
  setFatalError,
  markedComplete
}) => {
  const handleToggle = async (blockId, completed) => {
    console.log("🔍 Toggle debug:", { blockId, completed, lessonId });
    console.log("🔍 Current progress before toggle:", progress);
    console.log("🔍 Current markedComplete:", markedComplete);
    try {
      await updateLessonBlockProgress(lessonId, blockId, completed);
      console.log("🔍 API call successful, refreshing progress...");
      await refreshProgress(); // Refresh progress after each toggle
      await refreshCompletionStatus(); // Refresh completion status after each toggle
      console.log("🔍 Progress and completion status refreshed");
    } catch (err) {
      console.error("❌ Failed to update progress", err);
      setFatalError(true);
    }
  };

  if (entries.length === 0) {
    return <p>No content found.</p>;
  }

  return (
    <div className="space-y-4">
      {entries.map((entry, i) => (
        <Card key={i}>
          <h3 className="text-xl font-semibold">{entry.title}</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Added on {new Date(entry.created_at).toLocaleString()}
          </p>
          <BlockContentRenderer
            html={entry.content}
            progress={progress}
            mode="student"
            setFooterActions={setActions}
            onToggle={handleToggle}
          />
          {entry.ai_enabled && (
            <div className="mt-4">
              {showAi ? (
                <AIExerciseBlock
                  blockId={`lesson-${lessonId}-ai`}
                  setFooterActions={setActions}
                />
              ) : (
                <Button variant="secondary" onClick={() => setShowAi(true)}>
                  Start AI Exercises
                </Button>
              )}
            </div>
          )}
        </Card>
      ))}
    </div>
  );
};

export default LessonContent;

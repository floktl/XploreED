import React from "react";
import Card from "../UI/Card";
import ProgressRing from "../UI/ProgressRing";
import Spinner from "../UI/Spinner";

export default function AIWeaknessLessonProgress({
  progressPercentage,
  progressStatus,
  progressIcon
}) {
  return (
    <Card className="text-center py-8">
      <div className="flex justify-center mb-6">
        <ProgressRing
          percentage={progressPercentage}
          size={120}
          color={progressPercentage === 99 ? "#10B981" : "#3B82F6"}
        />
      </div>
      <div className="flex items-center justify-center gap-3 mb-4">
        {React.createElement(progressIcon, { className: "w-6 h-6 text-blue-600 dark:text-blue-400" })}
        <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
          {progressStatus}
        </h3>
      </div>
      <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
        {progressPercentage < 99
          ? "We're crafting a personalized lesson based on your weaknesses."
          : "Your personalized lesson is ready!"}
      </p>
      {progressPercentage < 99 && (
        <div className="mt-6 flex justify-center">
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <Spinner />
            <span>Please wait...</span>
          </div>
        </div>
      )}
    </Card>
  );
}

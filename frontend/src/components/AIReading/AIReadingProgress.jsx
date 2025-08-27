import React from "react";

export default function AIReadingProgress({ answers, questionsCount }) {
  const answeredCount = Object.keys(answers).filter(k => answers[k] && answers[k].trim && answers[k].trim().length > 0).length;
  const progressPercentage = (answeredCount / questionsCount) * 100;

  return (
    <div className="sticky top-16 z-30 w-full bg-white dark:bg-gray-900" style={{marginBottom: '1.5rem'}}>
      <div className="w-full h-2 rounded-full bg-gray-200 dark:bg-gray-800">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{
            width: `${progressPercentage}%`
          }}
        />
      </div>
    </div>
  );
}

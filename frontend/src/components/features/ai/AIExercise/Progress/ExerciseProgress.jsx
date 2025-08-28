import React, { useState, useEffect } from "react";
import ProgressRing from "../../../../common/UI/ProgressRing";
import { Brain, Target, BookOpen, Sparkles, CheckCircle } from "lucide-react";

export default function ExerciseProgress({
    loadingInit,
    progressPercentage,
    progressStatus,
    progressIcon
}) {
    if (!loadingInit) return null;

    return (
        <div className="flex flex-col items-center justify-center py-12">
            <ProgressRing
                percentage={progressPercentage}
                size={120}
                color="#3B82F6"
            />
            <div className="text-center">
                <div className="flex justify-center mb-4">
                    {progressIcon && React.createElement(progressIcon, { className: "w-8 h-8 text-blue-500" })}
                </div>
                <h3 className="text-lg font-semibold mb-2">Preparing Your Lesson</h3>
                <p className="text-gray-600 dark:text-gray-400">{progressStatus}</p>
            </div>
        </div>
    );
}

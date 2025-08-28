import ProgressRing from "../../../../common/UI/ProgressRing";
import { Brain, CheckCircle } from "lucide-react";

export default function SubmissionProgress({
    submitting,
    submissionProgress,
    submissionStatus
}) {
    if (!submitting) return null;

    return (
        <div className="flex flex-col items-center justify-center py-8">
            <ProgressRing
                progress={submissionProgress}
                size={80}
                strokeWidth={6}
                className="mb-4"
            />
            <div className="text-center">
                <div className="flex justify-center mb-2">
                    <Brain className="w-6 h-6 text-blue-500" />
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">{submissionStatus}</p>
            </div>
        </div>
    );
}

import React, { useState, useEffect } from "react";
import Card from "./UI/Card";
import Button from "./UI/Button";
import ProgressRing from "./UI/ProgressRing";
import Spinner from "./UI/Spinner";
import { Brain, CheckCircle, Target, BookOpen, Sparkles } from "lucide-react";

export default function ProgressTest() {
    const [currentTest, setCurrentTest] = useState(null);
    const [progressPercentage, setProgressPercentage] = useState(0);
    const [progressStatus, setProgressStatus] = useState("");
    const [progressIcon, setProgressIcon] = useState(Brain);

    const tests = [
        {
            name: "AI Exercise Generation",
            description: "Simulated progress for generating new exercises",
            steps: [
                { percentage: 15, status: "Analyzing your skill level...", icon: Target },
                { percentage: 35, status: "Reviewing your vocabulary...", icon: BookOpen },
                { percentage: 55, status: "Identifying weak areas...", icon: Brain },
                { percentage: 75, status: "Generating personalized exercises...", icon: Sparkles },
                { percentage: 90, status: "Finalizing your lesson...", icon: Sparkles },
                { percentage: 100, status: "Ready!", icon: CheckCircle }
            ],
            interval: 800
        },
        {
            name: "AI Feedback Generation",
            description: "Real backend progress for feedback generation",
            steps: [
                { percentage: 10, status: "Analyzing your answers...", icon: Target },
                { percentage: 30, status: "Evaluating answers with AI...", icon: Brain },
                { percentage: 50, status: "Processing evaluation results...", icon: BookOpen },
                { percentage: 70, status: "Fetching your vocabulary and progress data...", icon: BookOpen },
                { percentage: 85, status: "Generating personalized feedback...", icon: Sparkles },
                { percentage: 95, status: "Updating your learning progress...", icon: Sparkles },
                { percentage: 100, status: "Feedback generation complete!", icon: CheckCircle }
            ],
            interval: 600
        },
        {
            name: "Answer Submission",
            description: "Progress for submitting answers (shown in main content area)",
            steps: [
                { percentage: 20, status: "Analyzing your answers...", icon: Target },
                { percentage: 40, status: "Checking grammar and vocabulary...", icon: BookOpen },
                { percentage: 60, status: "Generating personalized feedback...", icon: Sparkles },
                { percentage: 80, status: "Preparing explanations...", icon: Brain },
                { percentage: 100, status: "Evaluation complete!", icon: CheckCircle }
            ],
            interval: 500
        }
    ];

    const runTest = (test) => {
        setCurrentTest(test);
        setProgressPercentage(0);
        setProgressStatus("Starting...");
        setProgressIcon(Brain);

        let currentStep = 0;
        const interval = setInterval(() => {
            if (currentStep < test.steps.length) {
                const step = test.steps[currentStep];
                setProgressPercentage(step.percentage);
                setProgressStatus(step.status);
                setProgressIcon(step.icon);
                currentStep++;
            } else {
                clearInterval(interval);
                setTimeout(() => {
                    setCurrentTest(null);
                    setProgressPercentage(0);
                    setProgressStatus("");
                }, 2000);
            }
        }, test.interval);
    };

    return (
        <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white p-8">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-3xl font-bold mb-8 text-center">Progress Bar Test</h1>

                {!currentTest ? (
                    <div className="grid gap-6 md:grid-cols-3">
                        {tests.map((test, index) => (
                            <Card key={index} className="p-6">
                                <h3 className="text-xl font-semibold mb-2">{test.name}</h3>
                                <p className="text-gray-600 dark:text-gray-400 mb-4">{test.description}</p>
                                <Button
                                    onClick={() => runTest(test)}
                                    variant="primary"
                                    className="w-full"
                                >
                                    Test Progress Bar
                                </Button>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <div className="text-center">
                        <Card className="p-8 max-w-md mx-auto">
                            <h2 className="text-2xl font-bold mb-6">{currentTest.name}</h2>

                            <div className="flex justify-center mb-6">
                                <ProgressRing
                                    percentage={progressPercentage}
                                    size={120}
                                    color={progressPercentage === 100 ? "#10B981" : "#3B82F6"}
                                />
                            </div>

                            <div className="flex items-center justify-center gap-3 mb-4">
                                {(() => {
                                    const IconComponent = progressIcon;
                                    return <IconComponent className="w-6 h-6 text-blue-600 dark:text-blue-400" />;
                                })()}
                                <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
                                    {progressStatus}
                                </h3>
                            </div>

                            <p className="text-gray-600 dark:text-gray-400 mb-4">
                                {progressPercentage < 100
                                    ? "Processing your request..."
                                    : "Complete!"
                                }
                            </p>

                            {progressPercentage < 100 && (
                                <div className="flex justify-center">
                                    <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                                        <Spinner />
                                        <span>Please wait...</span>
                                    </div>
                                </div>
                            )}

                            {progressPercentage === 100 && (
                                <div className="mt-4">
                                    <Button
                                        onClick={() => setCurrentTest(null)}
                                        variant="secondary"
                                    >
                                        Test Another
                                    </Button>
                                </div>
                            )}
                        </Card>
                    </div>
                )}
            </div>
        </div>
    );
}

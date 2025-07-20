import React from "react";
import useAppStore from "../../store/useAppStore";
import Spinner from "./Spinner";

interface ProgressRingProps {
    percentage: number;
    size?: number;
    color?: string;
}

export default function ProgressRing({
    percentage,
    size = 80,
    color = "#EF4444",
}: ProgressRingProps) {
    const darkMode = useAppStore((s) => s.darkMode);
    const radius = size / 2 - 4;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;
    const track = darkMode ? "#374151" : "#E5E7EB";
    const textColor = darkMode ? "#ffffff" : "#000000";

    return (
        <svg width={size} height={size} className="block">
            <circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                stroke={track}
                strokeWidth="4"
                fill="none"
            />
            <circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                stroke={color}
                strokeWidth="4"
                fill="none"
                strokeLinecap="round"
                strokeDasharray={`${circumference} ${circumference}`}
                strokeDashoffset={offset}
                transform={`rotate(-90 ${size / 2} ${size / 2})`}
            />
            {percentage === 99 ? (
                <foreignObject x="25%" y="25%" width="50%" height="50%">
                    <div className="flex items-center justify-center h-full">
                        <Spinner />
                    </div>
                </foreignObject>
            ) : (
                <text
                    x="50%"
                    y="50%"
                    textAnchor="middle"
                    dy=".3em"
                    fontSize={size * 0.25}
                    fill={textColor}
                    fontWeight="bold"
                >
                    {percentage}%
                </text>
            )}
        </svg>
    );
}

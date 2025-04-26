// ConfidenceIndicator.jsx
import React from "react";
import clsx from "clsx";
import useAppStore from "../../store/useAppStore";
import { Tooltip } from "react-tooltip";

/**
 * Displays an AI confidence indicator with a tooltip explanation
 * 
 * @param {number} confidence - Confidence score between 0-100
 * @param {string} tooltipId - Unique ID for the tooltip
 * @param {string} className - Additional CSS classes
 */
export default function ConfidenceIndicator({ confidence = 0, tooltipId = "confidence-tooltip", className = "" }) {
  const darkMode = useAppStore((state) => state.darkMode);
  
  // Determine color based on confidence level
  const getColorClass = () => {
    if (confidence >= 90) return darkMode ? "bg-green-600" : "bg-green-500";
    if (confidence >= 70) return darkMode ? "bg-blue-600" : "bg-blue-500";
    if (confidence >= 50) return darkMode ? "bg-yellow-600" : "bg-yellow-500";
    return darkMode ? "bg-red-600" : "bg-red-500";
  };
  
  // Get descriptive text for the confidence level
  const getConfidenceText = () => {
    if (confidence >= 90) return "High confidence";
    if (confidence >= 70) return "Good confidence";
    if (confidence >= 50) return "Moderate confidence";
    return "Low confidence";
  };
  
  // Get explanation text for the tooltip
  const getTooltipText = () => {
    if (confidence >= 90) {
      return "The AI is very confident in this translation and feedback.";
    }
    if (confidence >= 70) {
      return "The AI has good confidence in this translation, but there might be nuances it's unsure about.";
    }
    if (confidence >= 50) {
      return "The AI is moderately confident. Consider checking with other resources if this is important.";
    }
    return "The AI has low confidence in this translation. Consider consulting other resources.";
  };

  return (
    <div className={clsx("flex items-center", className)}>
      <div className="flex items-center mr-2">
        <div 
          data-tooltip-id={tooltipId}
          className={clsx(
            "h-2.5 w-2.5 rounded-full mr-1",
            getColorClass()
          )}
        />
        <span className={clsx(
          "text-xs font-medium",
          darkMode ? "text-gray-300" : "text-gray-600"
        )}>
          {getConfidenceText()}
        </span>
      </div>
      
      <Tooltip 
        id={tooltipId}
        place="top"
        content={getTooltipText()}
        className={clsx(
          "max-w-xs text-sm py-1 px-2 rounded shadow-lg",
          darkMode ? "bg-gray-700 text-white" : "bg-white text-gray-800 border border-gray-200"
        )}
      />
    </div>
  );
}

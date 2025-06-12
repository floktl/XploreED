// BlockContentRenderer.jsx
import React from "react";
import AIExerciseBlock from "./AIExerciseBlock";

export default function BlockContentRenderer({ html, progress = {}, onToggle }) {
  if (!html) {
    console.warn("⚠️ No HTML provided to BlockContentRenderer.");
    return <div className="text-sm text-gray-400 italic">No content</div>;
  }

  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = html;
  const children = Array.from(tempDiv.childNodes);
  const elements = [];

  children.forEach((node, index) => {
    const isInteractiveBlock =
      node.nodeType === Node.ELEMENT_NODE &&
      node.hasAttribute("data-task-block");

    const isAiExerciseBlock =
      node.nodeType === Node.ELEMENT_NODE &&
      node.hasAttribute("data-ai-exercise");

    if (isInteractiveBlock) {
      const blockId = node.getAttribute("data-block-id") || `block-${index}`;
      const isChecked = progress[blockId] ?? false;
      const contentText = node.textContent?.trim() || "No task description";
      const interactive = node.querySelector("input[type=checkbox]");

      elements.push(
        <div
          key={blockId}
          data-block-id={blockId}
          className="interactive-block rounded-xl p-4 space-y-4"
        >
          <div className="task-content text-gray-800 dark:text-white">{contentText}</div>
          <label className="flex items-center gap-2 pt-2 border-t border-gray-200 dark:border-gray-700 mt-2">
            <input
              type="checkbox"
              className="h-5 w-5 text-green-600 border-gray-300 rounded"
              data-interactive
              checked={isChecked}
              disabled={!onToggle}
              onChange={(e) => onToggle?.(blockId, e.target.checked)}
            />
            <span className="text-sm text-gray-600 dark:text-gray-300">Mark as complete</span>
          </label>
        </div>
      );
    } else if (isAiExerciseBlock) {
      let data = null;
      try {
        const encoded = node.getAttribute("data-ai-data") || "";
        data = JSON.parse(decodeURIComponent(encoded));
      } catch {}
      elements.push(<AIExerciseBlock key={`ai-${index}`} data={data} />);
    } else {
      elements.push(
        <div
          key={`html-${index}`}
          dangerouslySetInnerHTML={{
            __html: node.outerHTML || node.textContent,
          }}
        />
      );
    }
  });

  return <div className="prose dark:prose-invert space-y-4 mt-4">{elements}</div>;
}

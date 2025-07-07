// BlockContentRenderer.jsx
import React from "react";
import AIExerciseBlock from "./AIExerciseBlock";

export default function BlockContentRenderer({ html, progress = {}, onToggle, mode = "student", setFooterActions }) {
    if (!html) {
        console.warn("⚠️ No HTML provided to BlockContentRenderer.");
        return <div className="text-sm text-gray-400 italic">No content</div>;
    }

    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = html;
    const elements = [];

    const processNode = (node, keyPrefix = "") => {
        const index = elements.length;
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
                if (encoded) {
                    data = JSON.parse(decodeURIComponent(encoded));
                }
            } catch { }
            const blockId = node.getAttribute("data-block-id") || `ai-${index}`;
            const isCompleted = progress[blockId] ?? false;
            elements.push(
                <AIExerciseBlock
                    key={blockId}
                    data={data}
                    blockId={blockId}
                    completed={isCompleted}
                    onComplete={onToggle ? (() => onToggle(blockId, true)) : undefined}
                    mode={mode}
                    setFooterActions={setFooterActions}
                />
            );
        } else if (
            node.nodeType === Node.ELEMENT_NODE &&
            (node.querySelector("[data-ai-exercise]") ||
                node.querySelector("[data-task-block]"))
        ) {
            Array.from(node.childNodes).forEach((child) => processNode(child, keyPrefix));
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
    };

    Array.from(tempDiv.childNodes).forEach((node) => processNode(node));

    return <div className="prose dark:prose-invert space-y-4 mt-4">{elements}</div>;
}

export default function InteractiveBlock({
    blockId,
    isChecked,
    contentText,
    onToggle
}) {
    return (
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
}

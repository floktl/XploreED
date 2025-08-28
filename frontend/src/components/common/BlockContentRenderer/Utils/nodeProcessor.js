// Node processing utility for BlockContentRenderer

export const processNode = (node, elements, progress, onToggle, mode, setFooterActions, keyPrefix = "") => {
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

        elements.push({
            type: "interactive",
            key: blockId,
            blockId,
            isChecked,
            contentText,
            interactive
        });
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

        elements.push({
            type: "ai-exercise",
            key: blockId,
            data,
            blockId,
            isCompleted,
            mode,
            setFooterActions
        });
    } else if (
        node.nodeType === Node.ELEMENT_NODE &&
        (node.querySelector("[data-ai-exercise]") ||
            node.querySelector("[data-task-block]"))
    ) {
        Array.from(node.childNodes).forEach((child) =>
            processNode(child, elements, progress, onToggle, mode, setFooterActions, keyPrefix)
        );
    } else {
        elements.push({
            type: "html",
            key: `html-${index}`,
            html: node.outerHTML || node.textContent
        });
    }
};

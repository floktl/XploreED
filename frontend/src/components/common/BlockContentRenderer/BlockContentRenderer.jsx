
import AIExerciseBlock from "../../features/ai/AIExercise/AIExerciseBlock";
import { processNode } from "./Utils/nodeProcessor";
import InteractiveBlock from "./Components/InteractiveBlock";

export default function BlockContentRenderer({
    html,
    progress = {},
    onToggle,
    mode = "student",
    setFooterActions
}) {
    if (!html) {
        console.warn("⚠️ No HTML provided to BlockContentRenderer.");
        return <div className="text-sm text-gray-400 italic">No content</div>;
    }

    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = html;
    const elements = [];

    Array.from(tempDiv.childNodes).forEach((node) =>
        processNode(node, elements, progress, onToggle, mode, setFooterActions)
    );

    const renderElement = (element) => {
        switch (element.type) {
            case "interactive":
                return (
                    <InteractiveBlock
                        key={element.key}
                        blockId={element.blockId}
                        isChecked={element.isChecked}
                        contentText={element.contentText}
                        onToggle={onToggle}
                    />
                );
            case "ai-exercise":
                return (
                    <AIExerciseBlock
                        key={element.key}
                        data={element.data}
                        blockId={element.blockId}
                        completed={element.isCompleted}
                        onComplete={onToggle ? (() => onToggle(element.blockId, true)) : undefined}
                        mode={element.mode}
                        setFooterActions={element.setFooterActions}
                    />
                );
            case "html":
                return (
                    <div
                        key={element.key}
                        dangerouslySetInnerHTML={{
                            __html: element.html,
                        }}
                    />
                );
            default:
                return null;
        }
    };

    return (
        <div className="prose dark:prose-invert space-y-4 mt-4">
            {elements.map(renderElement)}
        </div>
    );
}

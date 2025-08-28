import { useState } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import Modal from "../../../common/UI/Modal";
import BlockContentRenderer from "../../../common/BlockContentRenderer/BlockContentRenderer";
import { getAiLesson } from "../../../../services/api";

// Import modular components
import EditorToolbar from "./Toolbar/EditorToolbar";
import { getEditorExtensions, getEditorProps } from "./Extensions/EditorExtensions";

export default function LessonEditor({ content, onContentChange, aiEnabled = false, onToggleAI }) {
    const [showPreview, setShowPreview] = useState(false);

    const editor = useEditor({
        extensions: getEditorExtensions(),
        content,
        editorProps: getEditorProps(),
        onUpdate: ({ editor }) => {
            onContentChange(editor.getHTML());
        },
    });

    if (!editor) return <div>Loading editor...</div>;

    const handleGenerateAI = async () => {
        try {
            const aiContent = await getAiLesson(content);
            if (aiContent && aiContent.exercises) {
                const exercisesHtml = aiContent.exercises
                    .map(ex => `<div data-ai-exercise data-ai-data="${encodeURIComponent(JSON.stringify(ex))}"></div>`)
                    .join('');
                const newContent = content + exercisesHtml;
                onContentChange(newContent);
                editor.commands.setContent(newContent);
            }
        } catch (error) {
            console.error("Failed to generate AI content:", error);
        }
    };

    return (
        <div className="border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
            <EditorToolbar
                editor={editor}
                aiEnabled={aiEnabled}
                onToggleAI={onToggleAI}
                onPreview={() => setShowPreview(true)}
                onGenerateAI={handleGenerateAI}
                showPreview={showPreview}
            />

            <div className="p-4">
                <EditorContent editor={editor} />
            </div>

            {showPreview && (
                <Modal onClose={() => setShowPreview(false)}>
                    <div className="max-w-4xl mx-auto">
                        <h2 className="text-xl font-semibold mb-4">Lesson Preview</h2>
                        <div className="prose dark:prose-invert max-w-none">
                            <BlockContentRenderer html={content} />
                        </div>
                    </div>
                </Modal>
            )}
        </div>
    );
}

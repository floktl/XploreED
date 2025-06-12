import React, { useState } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import Highlight from "@tiptap/extension-highlight";
import Placeholder from "@tiptap/extension-placeholder";
import CodeBlockLowlight from "@tiptap/extension-code-block-lowlight";
import { lowlight } from "lowlight";
import Table from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import Image from "@tiptap/extension-image";
import BulletList from "@tiptap/extension-bullet-list";
import OrderedList from "@tiptap/extension-ordered-list";
import ListItem from "@tiptap/extension-list-item";
import { TaskBlock } from "../extensions/TaskBlock";

import Modal from "./UI/Modal";
import BlockContentRenderer from "./BlockContentRenderer";

export default function LessonEditor({ content, onContentChange }) {
  const [showPreview, setShowPreview] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        codeBlock: false,
        bulletList: false,
        orderedList: false,
        listItem: false,
      }),
      BulletList,
      OrderedList,
      ListItem,
      Underline,
      Highlight,
      Placeholder.configure({
        placeholder: "Write your interactive lesson here...",
      }),
      CodeBlockLowlight.configure({ lowlight }),
      Table.configure({ resizable: true }),
      TableRow,
      TableCell,
      TableHeader,
      Image,
      TaskBlock,
    ],
    content,
    editorProps: {
      attributes: {
        class: "editor-wrapper focus:outline-none min-h-[300px]",
      },
    },
    onUpdate: ({ editor }) => {
      onContentChange(editor.getHTML());
    },
  });

  if (!editor) return <div>Loading editor...</div>;

  const generateBlockId = () =>
    "block-" + Math.random().toString(36).substring(2, 10);

  const insertInteractiveBlock = () => {
    const blockId = generateBlockId();
    editor
      .chain()
      .focus()
      .insertContent([
        {
          type: "taskBlock",
          attrs: {
            checked: false,
            block_id: blockId,
          },
          content: [
            {
              type: "paragraph",
              content: [
                {
                  type: "text",
                  text: "✍️ Describe your task here...",
                },
              ],
            },
          ],
        },
        { type: "paragraph" },
      ])
      .run();
  };

  const getLastTaskText = () => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(editor.getHTML(), "text/html");
    const blocks = doc.querySelectorAll("div[data-task-block]");
    if (blocks.length === 0) return null;
    return blocks[blocks.length - 1].textContent.trim();
  };


  const insertAiExercise = async () => {
    setAiLoading(true);
    try {
      const blockId = generateBlockId();
      const html = `<div data-ai-exercise="true" data-block-id="${blockId}">🤖 AI Exercise</div><p></p>`;
      editor.chain().focus().insertContent(html).run();
    } catch (err) {
      console.error("[LessonEditor] Failed to insert AI exercise placeholder", err);
      alert("Failed to insert AI exercise");
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div>
      {/* Toolbar */}
      <div className="flex flex-wrap gap-2 mb-3">
        <EditorButton
          onClick={() => editor.chain().focus().toggleBold().run()}
          active={editor.isActive("bold")}
        >
          <strong>B</strong>
        </EditorButton>
        <EditorButton
          onClick={() => editor.chain().focus().toggleItalic().run()}
          active={editor.isActive("italic")}
        >
          <em>I</em>
        </EditorButton>
        <EditorButton
          onClick={() => editor.chain().focus().toggleUnderline().run()}
          active={editor.isActive("underline")}
        >
          <u>U</u>
        </EditorButton>
        <EditorButton
          onClick={() => editor.chain().focus().toggleHighlight().run()}
          active={editor.isActive("highlight")}
        >
          <span className="bg-yellow-200">H</span>
        </EditorButton>
        <EditorButton
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          active={editor.isActive("codeBlock")}
        >
          {"</>"}
        </EditorButton>
        <EditorButton
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          active={editor.isActive("bulletList")}
        >
          • List
        </EditorButton>
        <EditorButton
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          active={editor.isActive("orderedList")}
        >
          1. List
        </EditorButton>
        <EditorButton
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 2 }).run()
          }
          active={editor.isActive("heading", { level: 2 })}
        >
          H2
        </EditorButton>
        <EditorButton
          onClick={() => {
            const url = prompt("Enter image URL");
            if (url) {
              editor.chain().focus().setImage({ src: url }).run();
            }
          }}
        >
          🖼️ Image
        </EditorButton>
        <EditorButton
          onClick={() =>
            editor
              .chain()
              .focus()
              .insertTable({ rows: 3, cols: 3, withHeaderRow: true })
              .run()
          }
        >
          📊 Table
        </EditorButton>
        <EditorButton onClick={insertInteractiveBlock}>✅ Block</EditorButton>
        <EditorButton onClick={insertAiExercise}>
          {aiLoading ? "🤖 Loading..." : "🤖 AI Exercise"}
        </EditorButton>
        <EditorButton onClick={() => setShowPreview(true)}>👁️ Preview</EditorButton>
      </div>

      {/* Editor */}
      <EditorContent
        editor={editor}
        className="border rounded-md p-4 dark:bg-gray-800 dark:text-white"
      />

      {/* Preview Modal */}
      {showPreview && (
        <Modal onClose={() => setShowPreview(false)}>
          <h2 className="text-xl font-bold mb-3">🔍 Lesson Preview</h2>
          <BlockContentRenderer html={editor.getHTML()} mode="admin-preview" />
        </Modal>
      )}
    </div>
  );
}

function EditorButton({ onClick, children, active }) {
  return (
    <button
      type="button"
      onMouseDown={(e) => e.preventDefault()} // prevents focus loss in editor
      onClick={onClick}
      className={`px-2 py-1 rounded border text-sm font-medium ${
        active
          ? "bg-blue-600 text-white"
          : "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-white"
      }`}
    >
      {children}
    </button>
  );
}

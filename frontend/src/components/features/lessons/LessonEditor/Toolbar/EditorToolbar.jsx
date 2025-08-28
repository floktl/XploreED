import Button from "../../../../common/UI/Button";
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Highlighter,
  Code2,
  List,
  ListOrdered,
  Heading2,
  Image as ImageIcon,
  Table as TableIcon,
  CheckSquare,
  Bot,
  Eye,
  BookOpen,
  Pencil,
  XCircle,
  Search
} from "lucide-react";

export default function EditorToolbar({
  editor,
  aiEnabled,
  onToggleAI,
  onPreview,
  onGenerateAI,
  showPreview
}) {
  if (!editor) return null;

  return (
    <div className="border-b border-gray-200 dark:border-gray-700 p-2 flex flex-wrap gap-1 items-center">
      {/* Text Formatting */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => editor.chain().focus().toggleBold().run()}
        className={editor.isActive('bold') ? 'bg-blue-100 dark:bg-blue-900' : ''}
      >
        <Bold className="w-4 h-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => editor.chain().focus().toggleItalic().run()}
        className={editor.isActive('italic') ? 'bg-blue-100 dark:bg-blue-900' : ''}
      >
        <Italic className="w-4 h-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => editor.chain().focus().toggleUnderline().run()}
        className={editor.isActive('underline') ? 'bg-blue-100 dark:bg-blue-900' : ''}
      >
        <UnderlineIcon className="w-4 h-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => editor.chain().focus().toggleHighlight().run()}
        className={editor.isActive('highlight') ? 'bg-blue-100 dark:bg-blue-900' : ''}
      >
        <Highlighter className="w-4 h-4" />
      </Button>

      {/* Divider */}
      <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />

      {/* Headings */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        className={editor.isActive('heading', { level: 2 }) ? 'bg-blue-100 dark:bg-blue-900' : ''}
      >
        <Heading2 className="w-4 h-4" />
      </Button>

      {/* Lists */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        className={editor.isActive('bulletList') ? 'bg-blue-100 dark:bg-blue-900' : ''}
      >
        <List className="w-4 h-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        className={editor.isActive('orderedList') ? 'bg-blue-100 dark:bg-blue-900' : ''}
      >
        <ListOrdered className="w-4 h-4" />
      </Button>

      {/* Divider */}
      <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />

      {/* Code */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => editor.chain().focus().toggleCodeBlock().run()}
        className={editor.isActive('codeBlock') ? 'bg-blue-100 dark:bg-blue-900' : ''}
      >
        <Code2 className="w-4 h-4" />
      </Button>

      {/* Table */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()}
      >
        <TableIcon className="w-4 h-4" />
      </Button>

      {/* Image */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => {
          const url = window.prompt('Enter image URL:');
          if (url) {
            editor.chain().focus().setImage({ src: url }).run();
          }
        }}
      >
        <ImageIcon className="w-4 h-4" />
      </Button>

      {/* Interactive Block */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => {
          const blockId = "block-" + Math.random().toString(36).substring(2, 10);
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
                        text: "Click to edit this interactive task...",
                      },
                    ],
                  },
                ],
              },
            ])
            .run();
        }}
      >
        <CheckSquare className="w-4 h-4" />
      </Button>

      {/* Divider */}
      <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />

      {/* AI Features */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onToggleAI}
        className={aiEnabled ? 'bg-green-100 dark:bg-green-900' : ''}
      >
        <Bot className="w-4 h-4" />
      </Button>
      {aiEnabled && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onGenerateAI}
        >
          <BookOpen className="w-4 h-4" />
        </Button>
      )}

      {/* Preview */}
      <Button
        variant="ghost"
        size="sm"
        onClick={onPreview}
        className={showPreview ? 'bg-blue-100 dark:bg-blue-900' : ''}
      >
        <Eye className="w-4 h-4" />
      </Button>
    </div>
  );
}

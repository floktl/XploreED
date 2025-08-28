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
import { TaskBlock } from "../../../../../extensions/TaskBlock";

export const getEditorExtensions = () => [
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
];

export const getEditorProps = () => ({
  attributes: {
    class: "editor-wrapper focus:outline-none min-h-[300px]",
  },
});

import { Node, mergeAttributes } from "@tiptap/core";

export const TaskBlock = Node.create({
    name: "taskBlock",

    group: "block",
    content: "block+",
    selectable: true,
    atom: false,

    addAttributes() {
        return {
            checked: {
                default: false,
                parseHTML: el => el.getAttribute("data-checked") === "true",
                renderHTML: attrs => ({
                    "data-checked": attrs.checked,
                }),
            },
            block_id: {
                default: null,
                parseHTML: el => el.getAttribute("data-block-id"),
                renderHTML: attrs => ({
                    "data-block-id": attrs.block_id,
                }),
            },
        };
    },


    parseHTML() {
        return [{ tag: "div[data-task-block]" }];
    },

    renderHTML({ HTMLAttributes }) {
        return [
            "div",
            mergeAttributes(HTMLAttributes, {
                "data-task-block": "true",
                class:
                    "interactive-block border border-gray-300 dark:border-gray-600 rounded-xl p-4 bg-white dark:bg-gray-800 shadow-sm space-y-4 mb-4",
            }),
            0, // Allow inner content to be rendered
        ];
    },

    addCommands() {
        return {
            insertTaskBlock:
                () =>
                    ({ commands }) => {
                        return commands.insertContent([
                            {
                                type: this.name,
                                attrs: { checked: false },
                                content: [
                                    {
                                        type: "paragraph",
                                        content: [{ type: "text", text: "✍️ Describe your task here..." }],
                                    },
                                ],
                            },
                            { type: "paragraph" }, // allow typing outside
                        ]);
                    },
        };
    },

    addNodeView() {
        return ({ node, editor, getPos }) => {
            const wrapper = document.createElement("div");
            wrapper.className =
                "interactive-block border border-gray-300 dark:border-gray-600 rounded-xl p-4 bg-white dark:bg-gray-800 shadow-sm space-y-4 mb-4";
            wrapper.setAttribute("data-task-block", "true");
            wrapper.setAttribute("data-checked", node.attrs.checked);

            // Main content container managed by Tiptap
            const contentDOM = document.createElement("div");
            contentDOM.className = "task-content min-h-[40px] text-gray-900 dark:text-white";

            // Checkbox container
            const label = document.createElement("label");
            label.className =
                "flex items-center gap-2 pt-2 border-t border-gray-200 dark:border-gray-700 mt-2";

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.checked = node.attrs.checked;
            checkbox.className = "h-5 w-5 text-green-600 border-gray-300 rounded";

            checkbox.addEventListener("change", (e) => {
                editor.commands.command(({ tr }) => {
                    tr.setNodeMarkup(getPos(), undefined, {
                        ...node.attrs,
                        checked: e.target.checked,
                    });
                    editor.view.dispatch(tr);
                    return true;
                });
            });

            const span = document.createElement("span");
            span.innerText = "Mark as complete";
            span.className = "text-gray-600 dark:text-gray-400 text-sm font-medium";

            label.appendChild(checkbox);
            label.appendChild(span);

            // Compose the full DOM
            wrapper.appendChild(contentDOM);
            wrapper.appendChild(label);

            return {
                dom: wrapper,
                contentDOM, // ✅ now Tiptap manages editable content properly
            };
        };
    },
});

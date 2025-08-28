import React, { useState, useRef, useEffect } from "react";
import useClickOutside from "../../utils/useClickOutside";
import ReactDOM from "react-dom";

interface DropdownProps {
    trigger: React.ReactNode;
    children: React.ReactNode;
}

export default function Dropdown({ trigger, children }: DropdownProps) {
    const [open, setOpen] = useState(false);
    const ref = useRef<HTMLDivElement>(null);
    const triggerRef = useRef<HTMLDivElement>(null);
    const menuRef = useRef<HTMLDivElement>(null);
    const [menuPos, setMenuPos] = useState<{top: number, left: number, width: number}>({top: 0, left: 0, width: 0});

    // Custom click outside for both trigger and menu
    useEffect(() => {
        if (!open) return;
        const handleClick = (e: MouseEvent) => {
            const trg = triggerRef.current;
            const menu = menuRef.current;
            if (
                trg && !trg.contains(e.target as Node) &&
                menu && !menu.contains(e.target as Node)
            ) {
                setOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClick);
        return () => document.removeEventListener("mousedown", handleClick);
    }, [open]);

    // Calculate position for portal menu
    useEffect(() => {
        if (open && triggerRef.current) {
            const rect = triggerRef.current.getBoundingClientRect();
            const menuWidth = 224; // Tailwind w-56 = 224px
            setMenuPos({
                top: rect.bottom + 8, // 8px margin
                left: rect.right - menuWidth,
                width: menuWidth
            });
        }
    }, [open]);

    return (
        <div className="relative" ref={ref}>
            <div
                ref={triggerRef}
                onClick={() => setOpen((prev) => !prev)}
                className="cursor-pointer select-none"
            >
                {trigger}
            </div>
            {open && ReactDOM.createPortal(
                <div
                    ref={menuRef}
                    className="rounded-xl shadow-xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 overflow-hidden z-[1000]"
                    style={{
                        position: 'fixed',
                        top: menuPos.top,
                        left: menuPos.left,
                        width: menuPos.width,
                        zIndex: 1000
                    }}
                >
                    {children}
                </div>,
                document.body
            )}
        </div>
    );
}

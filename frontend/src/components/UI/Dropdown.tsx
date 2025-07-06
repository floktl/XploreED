import React, { useState, useRef } from "react";
import useClickOutside from "../../utils/useClickOutside";

interface DropdownProps {
  trigger: React.ReactNode;
  children: React.ReactNode;
}

export default function Dropdown({ trigger, children }: DropdownProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useClickOutside(ref, () => setOpen(false));

  return (
    <div className="relative" ref={ref}>
      <div
        onClick={() => setOpen((prev) => !prev)}
        className="cursor-pointer select-none"
      >
        {trigger}
      </div>
      {open && (
        <div className="absolute right-0 mt-2 w-56 rounded-xl shadow-xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 overflow-hidden z-50">
          {children}
        </div>
      )}
    </div>
  );
}

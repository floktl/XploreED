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
      <button onClick={() => setOpen((o) => !o)} className="p-2 rounded-full bg-black/30 hover:bg-black/40">
        {trigger}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 bg-white dark:bg-gray-800 rounded-md shadow-md w-52 z-50">
          {children}
        </div>
      )}
    </div>
  );
}

import React from "react";
import Button from "../UI/Button";

export default function ThemeSection({ darkMode, onToggleDarkMode }) {
  return (
    <div className="space-y-2">
      <label className="block font-semibold">Theme</label>
      <Button variant="secondary" onClick={onToggleDarkMode}>
        {darkMode ? "Switch to Light" : "Switch to Dark"}
      </Button>
    </div>
  );
}

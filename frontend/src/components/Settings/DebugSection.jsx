import React from "react";
import Button from "../UI/Button";

export default function DebugSection({ debugEnabled, onToggleDebugEnabled }) {
  return (
    <div className="space-y-2">
      <label className="block font-semibold">Debug Features</label>
      <Button variant="secondary" onClick={onToggleDebugEnabled}>
        {debugEnabled ? "Disable Debug" : "Enable Debug"}
      </Button>
    </div>
  );
}

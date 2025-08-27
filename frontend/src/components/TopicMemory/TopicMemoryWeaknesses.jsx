import React from "react";
import ProgressRing from "../UI/ProgressRing";

export default function TopicMemoryWeaknesses({ weaknesses, getUrgencyColor }) {
  if (!weaknesses || weaknesses.length === 0) return null;

  return (
    <div className="mb-6 flex flex-col items-center gap-4">
      <p className="text-sm">Biggest weaknesses</p>
      <div className="flex gap-4">
        {weaknesses.map((w) => (
          <div key={w.grammar} className="flex flex-col items-center">
            <ProgressRing percentage={w.percent} size={70} color={getUrgencyColor(w.percent)} />
            <p className="mt-1 text-xs">{w.grammar}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

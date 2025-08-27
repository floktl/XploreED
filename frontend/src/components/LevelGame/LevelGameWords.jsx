import React from "react";

export default function LevelGameWords({
  currentOrder,
  draggedItem,
  hoverIndex,
  darkMode,
  onDragStart,
  onDragOver,
  onDragEnd,
  onDrop,
  onTouchStart,
  onTouchMove,
  onTouchEnd
}) {
  return (
    <div className="flex flex-wrap justify-center gap-2 mb-4 min-h-[60px] items-center">
      {Array.isArray(currentOrder) && currentOrder.map((word, i) => (
        <div
          key={i}
          data-index={i}
          draggable
          onDragStart={(e) => onDragStart(e, i)}
          onDragOver={(e) => onDragOver(e, i)}
          onDragEnd={onDragEnd}
          onDrop={(e) => onDrop(e, i)}
          onTouchStart={(e) => onTouchStart(e, i)}
          onTouchMove={onTouchMove}
          onTouchEnd={onTouchEnd}
          className={`word-item px-4 py-2 rounded-lg text-base font-medium transition-all duration-200 ${
            draggedItem === i
              ? "bg-blue-600 text-white shadow-lg z-10"
              : hoverIndex === i
              ? "bg-blue-400 text-white"
              : darkMode
              ? "bg-gray-700 hover:bg-gray-600 text-white"
              : "bg-gray-200 hover:bg-gray-300 text-gray-800"
          } cursor-ew-resize select-none flex items-center justify-center`}
          style={{ height: "42px" }}
        >
          {word}
        </div>
      ))}
    </div>
  );
}

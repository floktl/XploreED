import React from "react";

export default function TopicMemoryMobileCards({ filteredTopics, expandedCard, setExpandedCard, getUrgencyColor, easeToPercent }) {
  return (
    <div className="block sm:hidden space-y-3 mt-2">
      {filteredTopics.map((t) => (
        <div
          key={t.id}
          className="rounded-xl border p-3 shadow bg-white dark:bg-gray-800 cursor-pointer transition-all"
          style={{ borderColor: getUrgencyColor(easeToPercent(Number(t.ease_factor))) }}
          onClick={() => setExpandedCard(expandedCard === t.id ? null : t.id)}
        >
          <div className="flex flex-wrap gap-2 text-xs mb-1">
            <span className="font-semibold text-blue-700 dark:text-blue-300">Grammar:</span> {t.grammar || "-"}
          </div>
          <div className="flex flex-wrap gap-2 text-xs mb-1">
            <span className="font-semibold text-blue-700 dark:text-blue-300">Topic:</span> {t.topic || "-"}
          </div>
          <div className="flex flex-wrap gap-2 text-xs mb-1">
            <span className="font-semibold text-blue-700 dark:text-blue-300">Skill:</span> {t.skill_type}
          </div>
          {expandedCard === t.id && (
            <>
              <div className="flex flex-wrap gap-2 text-xs mb-1">
                <span className="font-semibold text-blue-700 dark:text-blue-300">Context:</span> {t.context}
              </div>
              <div className="flex flex-wrap gap-2 text-xs mb-1">
                <span className="font-semibold text-blue-700 dark:text-blue-300">Ease:</span> {Number(t.ease_factor).toFixed(2)}
              </div>
              <div className="flex flex-wrap gap-2 text-xs mb-1">
                <span className="font-semibold text-blue-700 dark:text-blue-300">Interval:</span> {t.intervall}
              </div>
              <div className="flex flex-wrap gap-2 text-xs mb-1">
                <span className="font-semibold text-blue-700 dark:text-blue-300">Next:</span> {t.next_repeat ? new Date(t.next_repeat).toLocaleDateString() : ""}
              </div>
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="font-semibold text-blue-700 dark:text-blue-300">Reps:</span> {t.repetitions}
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  );
}

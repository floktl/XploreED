import React from "react";
import { ChevronRight, ChevronDown } from "lucide-react";
import MenuItem from "./MenuItem";

export default function MenuSection({
  section,
  isExpanded,
  onToggle,
  onNavigate,
  darkMode
}) {
  const getColorClasses = (color) => {
    const colors = {
      blue: {
        bg: "bg-gray-50/50 dark:bg-gray-800/30",
        border: "border-gray-200 dark:border-gray-700",
        text: "text-gray-900 dark:text-gray-100",
        icon: "text-gray-600 dark:text-gray-300"
      },
      green: {
        bg: "bg-gray-50/50 dark:bg-gray-800/30",
        border: "border-gray-200 dark:border-gray-700",
        text: "text-gray-900 dark:text-gray-100",
        icon: "text-gray-600 dark:text-gray-300"
      },
      purple: {
        bg: "bg-gray-50/50 dark:bg-gray-800/30",
        border: "border-gray-200 dark:border-gray-700",
        text: "text-gray-900 dark:text-gray-100",
        icon: "text-gray-600 dark:text-gray-300"
      }
    };
    return colors[color] || colors.blue;
  };

  const colors = getColorClasses(section.color);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="p-6">
        {/* Section Header */}
        <button
          onClick={() => onToggle(section.id)}
          className="w-full flex items-center justify-between p-0 hover:opacity-80 transition-opacity"
        >
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-gray-100 dark:bg-gray-700">
              <section.icon className={`w-5 h-5 ${colors.icon}`} />
            </div>
            <div className="flex items-center space-x-2">
              <h2 className={`text-lg font-semibold ${colors.text}`}>
                {section.title}
              </h2>
              {section.id === "learning" && section.notifications && (section.notifications.newLessons > 0 || section.notifications.newWeaknessLessons > 0) && (
                <div className="flex-shrink-0">
                  <div className="bg-red-500 text-white text-xs font-medium px-2 py-1 rounded-full min-w-[20px] text-center">
                    {section.notifications.newLessons + section.notifications.newWeaknessLessons > 99 ? '99+' : section.notifications.newLessons + section.notifications.newWeaknessLessons}
                  </div>
                </div>
              )}
            </div>
          </div>
          {isExpanded ? (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronRight className="w-5 h-5 text-gray-400" />
          )}
        </button>

        {/* Section Items */}
        {isExpanded && (
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
            {section.items.map((item, index) => (
              <MenuItem
                key={index}
                item={item}
                darkMode={darkMode}
                onClick={() => onNavigate(item.path)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

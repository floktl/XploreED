import React from "react";

export default function MenuItem({ item, darkMode, onClick }) {
  return (
    <div
      onClick={onClick}
      className={`group cursor-pointer p-4 rounded-xl border border-gray-200 dark:border-gray-700 transition-all duration-200 hover:shadow-md hover:border-gray-300 dark:hover:border-gray-600 ${
        darkMode
          ? "bg-gray-800/50 hover:bg-gray-800"
          : "bg-gray-50/50 hover:bg-gray-50"
      }`}
    >
      <div className="flex flex-col space-y-3">
        <div className="flex items-center space-x-3">
          <div className={`p-2.5 rounded-xl ${
            item.variant === "primary"
              ? "bg-gray-100 dark:bg-gray-700"
              : "bg-gray-100 dark:bg-gray-700"
          }`}>
            <item.icon className={`w-5 h-5 ${
              item.variant === "primary"
                ? "text-gray-700 dark:text-gray-300"
                : "text-gray-600 dark:text-gray-400"
            }`} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center space-x-2">
              <h3 className="font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                {item.title}
              </h3>
              {item.notification > 0 && (
                <div className="flex-shrink-0">
                  <div className="bg-red-500 text-white text-xs font-medium px-2 py-1 rounded-full min-w-[20px] text-center">
                    {item.notification > 99 ? '99+' : item.notification}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        <p className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
          {item.description}
        </p>
      </div>
    </div>
  );
}

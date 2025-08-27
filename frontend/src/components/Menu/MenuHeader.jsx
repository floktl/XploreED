import React from "react";

export default function MenuHeader({ username, level = 3 }) {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
            Welcome back
          </h1>
          <p className="text-base font-medium text-gray-600 dark:text-gray-300 mt-1">
            {username}
          </p>
        </div>
        <div className="px-3 py-1.5 rounded-full text-sm font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700">
          Level {level}
        </div>
      </div>
    </div>
  );
}

import React from "react";
import clsx from "clsx";
import useAppStore from "../../store/useAppStore";

export const Input = ({ className, ...props }) => {
  const darkMode = useAppStore((state) => state.darkMode);

  return (
    <input
      {...props}
      className={clsx(
        "w-full px-4 py-2 rounded focus:outline-none focus:ring-2",
        darkMode
          ? "bg-gray-700 text-white border-gray-600 placeholder-gray-400 focus:ring-blue-500"
          : "bg-white text-gray-800 border-gray-300 placeholder-gray-500 focus:ring-blue-400",
        className
      )}
    />
  );
};

export const Title = ({ children, className }) => {
  const darkMode = useAppStore((state) => state.darkMode);

  return (
    <h1
      className={clsx(
        "text-3xl font-bold text-center mb-6",
        darkMode ? "text-blue-400" : "text-blue-800",
        className
      )}
    >
      {children}
    </h1>
  );
};

export const Container = ({ children, className }) => {
  const darkMode = useAppStore((state) => state.darkMode);

  return (
    <div
      className={clsx(
        "min-h-screen flex items-center justify-center px-4",
        darkMode ? "bg-gray-900" : "bg-gray-100"
      )}
    >
      <div
        className={clsx(
          "w-full max-w-2xl rounded-xl shadow-lg p-6",
          darkMode ? "bg-gray-800" : "bg-white",
          className
        )}
      >
        {children}
      </div>
    </div>
  );
};

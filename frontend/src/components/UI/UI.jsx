import React from "react";
import clsx from "clsx";
import useAppStore from "../../store/useAppStore";
import Header from "./Header";

export const Input = ({ className, ...props }) => {
  const darkMode = useAppStore((state) => state.darkMode);

  return (
    <input
      {...props}
      className={clsx(
        "w-full px-4 py-2 rounded border focus:outline-none focus:ring-2",
        darkMode
          ? "bg-gray-700 text-white border-gray-600 placeholder-gray-400 focus:ring-blue-500"
          : "bg-white text-gray-800 border-gray-100 placeholder-gray-500 focus:ring-blue-400",
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
    <>
      <Header />
      <div className="pt-20 pb-6 px-4 h-[calc(100vh-7rem)] flex flex-col">
        <div className="flex-1 overflow-auto flex flex-col items-center">
          <div
            className={clsx(
              "w-full max-w-4xl p-6 rounded-xl shadow-lg",
              darkMode ? "bg-gray-900/90" : "bg-white/90",
              className
            )}
          >
            {children}
          </div>
        </div>
      </div>
    </>
  );
};

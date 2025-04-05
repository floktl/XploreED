import React from "react";
import PropTypes from "prop-types";
import useAppStore from "../../store/useAppStore";

export default function Button({ type = "primary", className = "", onClick, children, ...props }) {
  const darkMode = useAppStore((state) => state.darkMode);

  const baseClass = "btn";

  const typeClass = {
    primary: darkMode ? "bg-blue-700 hover:bg-blue-600 text-white" : "bg-blue-500 hover:bg-blue-400 text-white",
    secondary: darkMode ? "bg-gray-600 hover:bg-gray-500 text-white" : "bg-gray-200 hover:bg-gray-300 text-gray-800",
    success: darkMode ? "bg-green-700 hover:bg-green-600 text-white" : "bg-green-500 hover:bg-green-400 text-white",
    danger: darkMode ? "bg-red-700 hover:bg-red-600 text-white" : "bg-red-500 hover:bg-red-400 text-white",
    link: darkMode ? "text-blue-400 hover:text-blue-300 underline bg-transparent" : "text-blue-600 hover:text-blue-500 underline bg-transparent",
  }[type];

  return (
    <button
      onClick={onClick}
      className={`${baseClass} ${typeClass} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

Button.propTypes = {
  type: PropTypes.oneOf(["primary", "secondary", "success", "danger", "link"]),
  className: PropTypes.string,
  onClick: PropTypes.func,
  children: PropTypes.node.isRequired,
};

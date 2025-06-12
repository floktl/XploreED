import React from "react";
import PropTypes from "prop-types";
import useAppStore from "../../store/useAppStore";

export default function Button({ variant = "primary", type = "button", className = "", onClick, disabled = false, children, ...props }) {
  const darkMode = useAppStore((state) => state.darkMode);

  const baseClass =
    "w-full px-4 py-2 rounded-lg font-semibold shadow-sm transition focus:outline-none flex items-center justify-center gap-2";

  const variantClass = {
    primary: darkMode ? "bg-blue-700 hover:bg-blue-600 text-white" : "bg-blue-500 hover:bg-blue-400 text-white",
    secondary: darkMode ? "bg-gray-600 hover:bg-gray-500 text-white" : "bg-gray-200 hover:bg-gray-300 text-gray-800",
    success: darkMode ? "bg-green-700 hover:bg-green-600 text-white" : "bg-green-500 hover:bg-green-400 text-white",
    danger: darkMode ? "bg-red-700 hover:bg-red-600 text-white" : "bg-red-500 hover:bg-red-400 text-white",
    link: darkMode
      ? "text-blue-400 hover:text-blue-300 underline bg-transparent justify-start"
      : "text-blue-600 hover:text-blue-500 underline bg-transparent justify-start",
    ghost: darkMode
      ? "bg-transparent text-white hover:bg-gray-800"
      : "bg-transparent text-gray-700 hover:bg-gray-100", // ✅ added ghost
    // Add this inside `variantClass`:
    progress: darkMode
      ? "bg-blue-900 text-white relative overflow-hidden"
      : "bg-blue-100 text-blue-800 relative overflow-hidden",

  }[variant];

  const disabledClass = "opacity-50 cursor-not-allowed pointer-events-none";

  const btnClass = `${baseClass} ${variantClass} ${disabled ? disabledClass : ""} ${className}`;
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={btnClass}
      {...props}
    >
      {children}
    </button>
  );
}

Button.propTypes = {
  variant: PropTypes.oneOf([
    "primary", "secondary", "success", "danger", "link", "ghost", "progress"  // ✅ added "progress"
  ]),
  type: PropTypes.oneOf(["button", "submit", "reset"]),
  className: PropTypes.string,
  onClick: PropTypes.func,
  disabled: PropTypes.bool,
  children: PropTypes.node.isRequired,
};

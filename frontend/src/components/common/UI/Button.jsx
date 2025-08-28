
import PropTypes from "prop-types";
import useAppStore from "../../../store/useAppStore";

export default function Button({
    variant = "primary",
    size = "md",
    type = "button",
    className = "",
    onClick,
    disabled = false,
    children,
    ...props
}) {
    const darkMode = useAppStore((state) => state.darkMode);

    const baseClass =
        "w-full px-4 py-2 rounded-lg font-semibold shadow-sm transition focus:outline-none flex items-center justify-center gap-2";

    const variantClass = {
        primary: darkMode ? "bg-blue-700 hover:bg-blue-600 text-white" : "bg-blue-500 hover:bg-blue-400 text-white",
        secondary: darkMode ? "bg-gray-600 hover:bg-gray-500 text-white" : "bg-gray-200 hover:bg-gray-300 text-gray-800",
        success: darkMode ? "bg-green-700 hover:bg-green-600 text-white" : "bg-green-500 hover:bg-green-400 text-white",
        successBright: darkMode ? "bg-green-500 hover:bg-green-400 text-white" : "bg-green-400 hover:bg-green-300 text-white",
        danger: darkMode ? "bg-red-700 hover:bg-red-600 text-white" : "bg-red-500 hover:bg-red-400 text-white",
        link: darkMode
            ? "text-blue-400 hover:text-blue-300 underline bg-transparent justify-start"
            : "text-blue-600 hover:text-blue-500 underline bg-transparent justify-start",
        ghost: darkMode
            ? "bg-transparent text-white hover:bg-gray-800"
            : "bg-transparent text-gray-700 hover:bg-gray-100",
        progress: darkMode
            ? "bg-blue-900 text-white relative overflow-hidden"
            : "bg-blue-100 text-blue-800 relative overflow-hidden"
    }[variant];

    const sizeClass = {
        sm: "px-2 py-1 text-sm w-auto",
        md: "px-4 py-2 text-base w-full",
        lg: "px-6 py-3 text-lg w-full",
        auto: "px-4 py-2 text-base w-auto"
    }[size];

    const disabledClass = "opacity-50 cursor-not-allowed pointer-events-none";

    const btnClass = `${baseClass} ${variantClass} ${sizeClass} ${disabled ? disabledClass : ""} ${className}`;
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
        "primary", "secondary", "success", "successBright", "danger", "link", "ghost", "progress"  // ✅ added "progress"
    ]),
    type: PropTypes.oneOf(["button", "submit", "reset"]),
    className: PropTypes.string,
    onClick: PropTypes.func,
    disabled: PropTypes.bool,
    children: PropTypes.node.isRequired,
};

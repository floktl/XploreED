import useAppStore from "../../../store/useAppStore";

const PageLayout = ({
  children,
  variant = "default",
  className = "",
  showPadding = true,
  showBottomPadding = true,
  overflowHidden = false
}) => {
  const darkMode = useAppStore((state) => state.darkMode);

  const baseClasses = "min-h-screen";

  const variantClasses = {
    default: `${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`,
    flex: `flex flex-col ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`,
    relative: `relative ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`,
    centered: "flex items-center justify-center",
    error: "flex items-center justify-center p-6"
  };

  const paddingClasses = showPadding ? "pb-20" : "";
  const overflowClasses = overflowHidden ? "overflow-x-hidden" : "";

  const layoutClasses = [
    baseClasses,
    variantClasses[variant] || variantClasses.default,
    paddingClasses,
    overflowClasses,
    className
  ].filter(Boolean).join(" ");

  return (
    <div className={layoutClasses}>
      {children}
    </div>
  );
};

export default PageLayout;

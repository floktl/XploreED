import React from "react";

export default function Footer({ children }) {
    return (
        <footer
            className="fixed bottom-0 left-0 w-full px-4 z-50 flex items-center justify-between border-t border-white/10 backdrop-blur-md bg-white/10 text-xs text-white/90 min-h-[48px] max-h-[56px]"
        >
            <div className="flex items-center gap-2 w-full h-full">
                {React.Children.map(children, child =>
                    React.isValidElement(child)
                        ? React.cloneElement(child, { className: `${child.props.className || ''} h-10 my-0 py-0` })
                        : child
                )}
            </div>
        </footer>
    );
}

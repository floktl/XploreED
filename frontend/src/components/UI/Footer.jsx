import React, { useEffect, useState } from "react";
import useAppStore from "../../store/useAppStore";

export default function Footer({ children }) {
    const [visible, setVisible] = useState(true);
    const [viewportHeight, setViewportHeight] = useState(window.innerHeight);

    useEffect(() => {
        const setFooterVisible = useAppStore.getState().setFooterVisible;
        setFooterVisible(true);
        const handleFocusIn = (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
                setVisible(false);
                setFooterVisible(false);
            }
        };
        const handleFocusOut = (e) => {
            setTimeout(() => {
                if (!document.activeElement || (document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA' && !document.activeElement.isContentEditable)) {
                    setVisible(true);
                    setFooterVisible(true);
                }
            }, 100);
        };
        document.addEventListener('focusin', handleFocusIn);
        document.addEventListener('focusout', handleFocusOut);

        // Visual viewport logic
        let lastHeight = window.innerHeight;
        const handleViewportResize = () => {
            const vvh = window.visualViewport ? window.visualViewport.height : window.innerHeight;
            setViewportHeight(vvh);
            // Hide footer if viewport height is less than 80% of window height (keyboard likely open)
            if (vvh < window.innerHeight * 0.8) {
                setVisible(false);
                setFooterVisible(false);
            } else {
                setVisible(true);
                setFooterVisible(true);
            }
            lastHeight = vvh;
        };
        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', handleViewportResize);
        } else {
            window.addEventListener('resize', handleViewportResize);
        }

        return () => {
            document.removeEventListener('focusin', handleFocusIn);
            document.removeEventListener('focusout', handleFocusOut);
            if (window.visualViewport) {
                window.visualViewport.removeEventListener('resize', handleViewportResize);
            } else {
                window.removeEventListener('resize', handleViewportResize);
            }
            setFooterVisible(false);
        };
    }, []);

    if (!children || !visible) return null;
    return (
        <footer
            className="fixed bottom-0 left-0 w-full px-2 z-50 flex items-center justify-between border-t border-white/10 backdrop-blur-md bg-white/10 text-xs text-white/90 min-h-[48px] max-h-[56px] transition-opacity duration-200"
            style={{ opacity: visible ? 1 : 0 }}
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

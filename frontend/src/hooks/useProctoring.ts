"use client";

import { useEffect, useRef } from "react";

interface ProctoringCallbacks {
    onTabSwitch?: () => void;
    onCopy?: () => void;
    onPaste?: () => void;
    onVisibilityChange?: (isVisible: boolean) => void;
}

export function useProctoring(callbacks: ProctoringCallbacks) {
    const alertCountRef = useRef(0);

    useEffect(() => {
        // Disable copy
        const handleCopy = (e: ClipboardEvent) => {
            e.preventDefault();
            callbacks.onCopy?.();
            alertCountRef.current++;
        };

        // Disable paste
        const handlePaste = (e: ClipboardEvent) => {
            e.preventDefault();
            callbacks.onPaste?.();
            alertCountRef.current++;
        };

        // Disable cut
        const handleCut = (e: ClipboardEvent) => {
            e.preventDefault();
        };

        // Detect tab switching / window blur
        const handleBlur = () => {
            callbacks.onTabSwitch?.();
            callbacks.onVisibilityChange?.(false);
            alertCountRef.current++;
        };

        const handleFocus = () => {
            callbacks.onVisibilityChange?.(true);
        };

        // Detect visibility change (tab switching, minimizing, etc.)
        const handleVisibilityChange = () => {
            if (document.hidden) {
                callbacks.onVisibilityChange?.(false);
                callbacks.onTabSwitch?.();
                alertCountRef.current++;
            } else {
                callbacks.onVisibilityChange?.(true);
            }
        };

        // Disable right-click context menu
        const handleContextMenu = (e: MouseEvent) => {
            e.preventDefault();
        };

        // Disable keyboard shortcuts
        const handleKeyDown = (e: KeyboardEvent) => {
            // Disable Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A, Ctrl+S, F12, etc.
            if (
                (e.ctrlKey || e.metaKey) &&
                (e.key === "c" || e.key === "v" || e.key === "x" || e.key === "a" || e.key === "s")
            ) {
                e.preventDefault();
                if (e.key === "c") callbacks.onCopy?.();
                if (e.key === "v") callbacks.onPaste?.();
            }

            // Disable F12 (DevTools)
            if (e.key === "F12" || (e.ctrlKey && e.shiftKey && e.key === "I")) {
                e.preventDefault();
            }
        };

        // Disable text selection
        const handleSelectStart = (e: Event) => {
            e.preventDefault();
        };

        // Add event listeners
        document.addEventListener("copy", handleCopy);
        document.addEventListener("paste", handlePaste);
        document.addEventListener("cut", handleCut);
        document.addEventListener("contextmenu", handleContextMenu);
        document.addEventListener("keydown", handleKeyDown);
        document.addEventListener("selectstart", handleSelectStart);
        window.addEventListener("blur", handleBlur);
        window.addEventListener("focus", handleFocus);
        document.addEventListener("visibilitychange", handleVisibilityChange);

        // Disable text selection via CSS
        document.body.style.userSelect = "none";
        document.body.style.webkitUserSelect = "none";

        return () => {
            document.removeEventListener("copy", handleCopy);
            document.removeEventListener("paste", handlePaste);
            document.removeEventListener("cut", handleCut);
            document.removeEventListener("contextmenu", handleContextMenu);
            document.removeEventListener("keydown", handleKeyDown);
            document.removeEventListener("selectstart", handleSelectStart);
            window.removeEventListener("blur", handleBlur);
            window.removeEventListener("focus", handleFocus);
            document.removeEventListener("visibilitychange", handleVisibilityChange);
            document.body.style.userSelect = "";
            document.body.style.webkitUserSelect = "";
        };
    }, [callbacks]);

    return { alertCount: alertCountRef.current };
}

import React from "react"
import Editor from "@monaco-editor/react"

interface CodeEditorPanelProps {
    language: string
    monacoLanguage: string
    code: string
    onCodeChange: (code: string) => void
    isReadOnly: boolean
}

export default function CodeEditorPanel({
    language,
    monacoLanguage,
    code,
    onCodeChange,
    isReadOnly,
}: CodeEditorPanelProps) {
    const handleEditorChange = (value: string | undefined) => {
        onCodeChange(value || "")
    }

    return (
        <div className="relative w-full h-full bg-[#1e1e2e]">
            <Editor
                height="100%"
                language={monacoLanguage}
                theme="vs-dark"
                value={code}
                onChange={handleEditorChange}
                options={{
                    readOnly: isReadOnly,
                    minimap: { enabled: false },
                    fontSize: 14,
                    fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace",
                    fontLigatures: true,
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    padding: { top: 16, bottom: 16 },
                    renderLineHighlight: "all",
                    matchBrackets: "always",
                    cursorBlinking: "smooth",
                    cursorSmoothCaretAnimation: "on",
                    smoothScrolling: true,
                    bracketPairColorization: { enabled: true },
                    guides: {
                        bracketPairs: true,
                        indentation: true,
                    },
                    lineNumbers: "on",
                    glyphMargin: false,
                    folding: true,
                    lineDecorationsWidth: 10,
                    lineNumbersMinChars: 3,
                    renderWhitespace: "none",
                    wordWrap: "off",
                    suggest: {
                        showKeywords: true,
                        showSnippets: true,
                    },
                }}
            />
            {isReadOnly && (
                <div className="absolute inset-0 bg-[#1e1e2e]/50 z-10 pointer-events-none flex items-center justify-center backdrop-blur-[1px]">
                    <div className="bg-emerald-500 text-white px-6 py-2 rounded-full shadow-lg shadow-emerald-500/20 text-sm font-bold tracking-wide">
                        ✓ Solution Submitted — View Only
                    </div>
                </div>
            )}
        </div>
    )
}

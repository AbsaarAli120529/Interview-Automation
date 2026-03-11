import React, { useEffect, useRef, useState, useCallback } from "react"
import { useCodingStore } from "@/store/codingStore"
import { useInterviewStore } from "@/store/interviewStore"
import ProblemPanel from "@/components/coding/ProblemPanel"
import CodeEditorPanel from "@/components/coding/CodeEditorPanel"
import ResultsPanel from "@/components/coding/ResultsPanel"
import Timer from "./Timer"
import VideoFeed from "./VideoFeed"

interface CodingQuestionProps {
    question: any;
    interviewId?: string | null;
}

export default function CodingQuestion({ question, interviewId }: CodingQuestionProps) {
    const {
        setProblemFromInterview,
        problem,
        language,
        code,
        setCode,
        setLanguage,
        results,
        resultSummary,
        isRunning,
        isSubmitting,
        isSubmitted,
        submissionStatus,
        error,
        runCurrentCode,
        submitCurrentCode,
    } = useCodingStore()

    const [resultsHeight, setResultsHeight] = useState(200)
    const [isResizing, setIsResizing] = useState(false)
    const [showResults, setShowResults] = useState(true)
    const resizeRef = useRef<HTMLDivElement>(null)

    const supportedLanguages = [
        { label: "Python 3", value: "python3", monaco: "python" },
        { label: "JavaScript", value: "javascript", monaco: "javascript" },
        { label: "Java", value: "java", monaco: "java" },
        { label: "C++", value: "cpp", monaco: "cpp" },
    ]

    const currentMonacoLang = supportedLanguages.find(l => l.value === language)?.monaco || "python"

    useEffect(() => {
        if (question) {
            setProblemFromInterview(question)
        }
    }, [question, setProblemFromInterview])

    // Auto-show results when results come in
    useEffect(() => {
        if (results.length > 0 || error) {
            setShowResults(true)
        }
    }, [results, error])

    // Resizable panel logic
    const handleMouseDown = useCallback((e: React.MouseEvent) => {
        e.preventDefault()
        setIsResizing(true)
    }, [])

    useEffect(() => {
        if (!isResizing) return

        const handleMouseMove = (e: MouseEvent) => {
            const rightPane = document.getElementById("coding-right-pane")
            if (!rightPane) return
            const rect = rightPane.getBoundingClientRect()
            const newHeight = rect.bottom - e.clientY
            setResultsHeight(Math.max(100, Math.min(newHeight, rect.height - 150)))
        }

        const handleMouseUp = () => {
            setIsResizing(false)
        }

        document.addEventListener("mousemove", handleMouseMove)
        document.addEventListener("mouseup", handleMouseUp)
        return () => {
            document.removeEventListener("mousemove", handleMouseMove)
            document.removeEventListener("mouseup", handleMouseUp)
        }
    }, [isResizing])

    const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setLanguage(e.target.value)
    }

    const handleRun = () => {
        runCurrentCode()
    }

    const handleSubmit = () => {
        submitCurrentCode(interviewId || undefined)
    }

    if (!problem) return (
        <div className="flex items-center justify-center h-screen bg-[#1a1a2e] animate-pulse">
            <div className="flex flex-col items-center gap-3">
                <div className="w-10 h-10 border-2 border-[#4a9eff] border-t-transparent rounded-full animate-spin" />
                <span className="text-[#8b8fa3] text-sm font-medium tracking-wide">Loading problem…</span>
            </div>
        </div>
    )

    return (
        <div className="fixed inset-0 z-50 flex flex-col bg-[#1a1a2e] text-[#e4e4e7]" style={{ fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif" }}>
            {/* ─── Top Navbar ─── */}
            <nav className="h-12 flex items-center justify-between px-4 bg-[#16162a] border-b border-[#2a2a4a] shrink-0 select-none">
                {/* Left: Section label + Timer */}
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <svg className="w-5 h-5 text-[#4a9eff]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                        </svg>
                        <span className="text-sm font-semibold text-[#c4c4cc] tracking-wide">Coding Challenge</span>
                    </div>
                    <div className="h-5 w-px bg-[#2a2a4a]" />
                    <Timer durationSec={question.time_limit_sec} onExpire={handleSubmit} />
                </div>

                {/* Center: Language selector */}
                <div className="flex items-center">
                    <select
                        value={language}
                        onChange={handleLanguageChange}
                        disabled={isSubmitted || isSubmitting || isRunning}
                        className="bg-[#252545] text-[#c4c4cc] border border-[#3a3a5a] rounded-md px-3 py-1.5 text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-[#4a9eff] focus:border-[#4a9eff] disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer appearance-none pr-7"
                        style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%238b8fa3' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 8px center' }}
                    >
                        {supportedLanguages.map(l => (
                            <option key={l.value} value={l.value}>{l.label}</option>
                        ))}
                    </select>
                </div>

                {/* Right: Run + Submit buttons */}
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleRun}
                        disabled={isSubmitted || isSubmitting || isRunning}
                        className="px-4 py-1.5 bg-[#252545] text-[#c4c4cc] text-xs font-bold rounded-md border border-[#3a3a5a] hover:bg-[#30305a] hover:border-[#4a4a6a] disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150 flex items-center gap-2"
                    >
                        {isRunning ? (
                            <div className="w-3 h-3 border-2 border-[#c4c4cc] border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4l12 6-12 6V4z" /></svg>
                        )}
                        {isRunning ? "Running…" : "Run"}
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={isSubmitted || isSubmitting || isRunning}
                        className="px-4 py-1.5 bg-[#1a8f4a] text-white text-xs font-bold rounded-md hover:bg-[#1fa855] disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150 flex items-center gap-2 shadow-sm shadow-[#1a8f4a]/20"
                    >
                        {isSubmitting ? (
                            <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>
                        )}
                        {isSubmitting ? "Submitting…" : "Submit"}
                    </button>
                </div>
            </nav>

            {/* ─── Main Body: Two Panes ─── */}
            <div className="flex-1 flex overflow-hidden">
                {/* Left Pane: Problem Description */}
                <div className="w-[45%] border-r border-[#2a2a4a] flex flex-col overflow-hidden">
                    {/* Problem header */}
                    <div className="px-5 py-3 border-b border-[#2a2a4a] flex items-center justify-between bg-[#1e1e38] shrink-0">
                        <h2 className="text-base font-semibold text-[#e4e4e7] truncate">{problem.title}</h2>
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase ${problem.difficulty.toLowerCase() === 'easy' ? 'text-emerald-400 bg-emerald-400/10 ring-1 ring-emerald-400/20' :
                                problem.difficulty.toLowerCase() === 'medium' ? 'text-amber-400 bg-amber-400/10 ring-1 ring-amber-400/20' :
                                    'text-rose-400 bg-rose-400/10 ring-1 ring-rose-400/20'
                            }`}>
                            {problem.difficulty}
                        </span>
                    </div>
                    {/* Problem body */}
                    <div className="flex-1 overflow-y-auto p-5 space-y-6 coding-scrollbar bg-[#1a1a2e]">
                        <div className="prose prose-sm prose-invert max-w-none text-[#a8a8b8] leading-relaxed whitespace-pre-wrap" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
                            {problem.description}
                        </div>

                        {problem.examples && problem.examples.length > 0 && (
                            <div className="space-y-4">
                                {problem.examples.map((ex: any, idx: number) => (
                                    <div key={idx} className="space-y-2">
                                        <h3 className="text-sm font-semibold text-[#c4c4cc]">Example {idx + 1}:</h3>
                                        <div className="bg-[#12122a] rounded-lg p-4 border border-[#2a2a4a] text-sm font-mono leading-relaxed space-y-1.5">
                                            <div>
                                                <span className="font-bold text-[#7aa2f7]">Input: </span>
                                                <span className="text-[#a8a8b8]">{ex.input}</span>
                                            </div>
                                            <div>
                                                <span className="font-bold text-[#9ece6a]">Output: </span>
                                                <span className="text-[#a8a8b8]">{ex.expected_output}</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Pane: Editor + Results */}
                <div id="coding-right-pane" className="flex-1 flex flex-col overflow-hidden bg-[#1e1e2e]">
                    {/* Code Editor */}
                    <div className="flex-1 overflow-hidden min-h-[150px]">
                        <CodeEditorPanel
                            language={language}
                            monacoLanguage={currentMonacoLang}
                            code={code}
                            onCodeChange={setCode}
                            isReadOnly={isSubmitted}
                        />
                    </div>

                    {/* Resize Handle */}
                    {showResults && (
                        <div
                            ref={resizeRef}
                            onMouseDown={handleMouseDown}
                            className={`h-1.5 shrink-0 cursor-row-resize flex items-center justify-center transition-colors ${isResizing ? 'bg-[#4a9eff]' : 'bg-[#2a2a4a] hover:bg-[#3a3a5a]'
                                }`}
                        >
                            <div className="w-8 h-0.5 rounded-full bg-[#555580]" />
                        </div>
                    )}

                    {/* Results Panel */}
                    {showResults && (
                        <div style={{ height: resultsHeight }} className="shrink-0 overflow-hidden">
                            <ResultsPanel
                                results={results}
                                summary={resultSummary}
                                isRunning={isRunning}
                                isSubmitting={isSubmitting}
                                error={error}
                                submissionStatus={submissionStatus}
                            />
                        </div>
                    )}

                    {/* Toggle Results */}
                    {!showResults && (
                        <button
                            onClick={() => setShowResults(true)}
                            className="h-8 shrink-0 bg-[#1e1e38] border-t border-[#2a2a4a] text-[#8b8fa3] text-xs font-medium flex items-center justify-center gap-1.5 hover:bg-[#252545] hover:text-[#c4c4cc] transition-colors"
                        >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" /></svg>
                            Show Console
                        </button>
                    )}
                </div>
            </div>

            {/* ─── Bottom-Left: Circular Video Feed ─── */}
            <div className="fixed bottom-5 left-5 z-[60] group">
                <div className="w-28 h-28 rounded-full overflow-hidden ring-2 ring-[#4a9eff]/50 shadow-lg shadow-black/40 bg-[#16162a]">
                    <VideoFeed />
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full ring-2 ring-[#1a1a2e] animate-pulse" />
            </div>

            {/* ─── Global Styles ─── */}
            <style jsx>{`
                .coding-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }
                .coding-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .coding-scrollbar::-webkit-scrollbar-thumb {
                    background: #3a3a5a;
                    border-radius: 3px;
                }
                .coding-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #4a4a6a;
                }
            `}</style>
        </div>
    )
}

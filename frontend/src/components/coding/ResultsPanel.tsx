import React from "react"
import { TestCaseResult } from "@/lib/api/codingApi"

interface ResultsPanelProps {
    results: TestCaseResult[]
    summary: { passed: number; total: number } | null
    isRunning: boolean
    isSubmitting: boolean
    error: string | null
    submissionStatus: "passed" | "failed" | "error" | null
}

export default function ResultsPanel({
    results,
    summary,
    isRunning,
    isSubmitting,
    error,
    submissionStatus
}: ResultsPanelProps) {
    if (isRunning || isSubmitting) {
        return (
            <div className="flex flex-col items-center justify-center h-full bg-[#1a1a2e] border-t border-[#2a2a4a]">
                <div className="animate-spin rounded-full h-6 w-6 border-2 border-emerald-500 border-t-transparent mb-3"></div>
                <p className="text-xs text-[#8b8fa3] font-medium">
                    {isSubmitting ? "Judging…" : "Running Tests…"}
                </p>
            </div>
        )
    }

    if (error) {
        return (
            <div className="h-full p-4 bg-[#1a1a2e] border-t border-[#2a2a4a] overflow-y-auto results-scrollbar">
                <h3 className="text-sm font-bold text-rose-400 mb-2 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>
                    Execution Error
                </h3>
                <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-md font-mono text-xs text-rose-300 whitespace-pre-wrap leading-relaxed">
                    {error}
                </div>
            </div>
        )
    }

    if (!results || results.length === 0) {
        return (
            <div className="flex items-center justify-center h-full bg-[#1a1a2e] border-t border-[#2a2a4a] text-[#555580] text-xs">
                <div className="flex flex-col items-center gap-2">
                    <svg className="w-8 h-8 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                    <span>Run your code to see results here</span>
                </div>
            </div>
        )
    }

    const allPassed = summary && summary.passed === summary.total
    const isAccepted = submissionStatus === 'passed'

    return (
        <div className="flex flex-col h-full bg-[#1a1a2e] border-t border-[#2a2a4a] overflow-hidden">
            <div className="px-4 py-2 flex items-center justify-between border-b border-[#2a2a4a] bg-[#1e1e38] shrink-0">
                <div className="flex items-center gap-3">
                    <h3 className="text-xs font-semibold text-[#c4c4cc] uppercase tracking-wider">Console</h3>
                    {summary && (
                        <span className="text-xs font-bold text-[#8b8fa3]">
                            {summary.passed}/{summary.total} Passed
                        </span>
                    )}
                </div>

                {submissionStatus && (
                    <span className={`text-sm font-bold tracking-tight ${isAccepted ? 'text-emerald-400' :
                        submissionStatus === 'failed' ? 'text-rose-400' :
                            'text-amber-400'
                        }`}>
                        {isAccepted ? '✓ Accepted' : submissionStatus === 'failed' ? '✗ Wrong Answer' : '⚠ Error'}
                    </span>
                )}
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-3 results-scrollbar">
                {!submissionStatus && summary && (
                    <div className={`text-lg font-bold ${allPassed ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {allPassed ? '✓ Accepted' : '✗ Wrong Answer'}
                    </div>
                )}

                <div className="space-y-3">
                    {results.map((res, idx) => (
                        <div key={idx} className="space-y-2">
                            <div className="flex items-center gap-2">
                                <span className={`px-2 py-0.5 rounded text-xs font-bold ${res.passed ? 'text-emerald-400 bg-emerald-400/10' : 'text-rose-400 bg-rose-400/10'}`}>
                                    Case {idx + 1}: {res.passed ? 'Accepted' : 'Wrong Answer'}
                                </span>
                            </div>

                            <div className="space-y-2 bg-[#12122a] rounded-md p-3 border border-[#2a2a4a] text-xs font-mono text-[#c4c4cc]">
                                <div>
                                    <p className="text-[#8b8fa3] mb-1 text-[10px] uppercase font-sans font-semibold tracking-wider">Input</p>
                                    <div className="bg-[#0e0e20] p-2 rounded text-[#c4c4cc] break-words">{res.input}</div>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    <div>
                                        <p className="text-[#8b8fa3] mb-1 text-[10px] uppercase font-sans font-semibold tracking-wider">Output</p>
                                        <div className={`p-2 rounded break-words ${res.passed ? 'bg-[#0e0e20]' : 'bg-rose-500/10 text-rose-300'}`}>{res.actual_output}</div>
                                    </div>
                                    {!res.passed && !res.error && (
                                        <div>
                                            <p className="text-[#8b8fa3] mb-1 text-[10px] uppercase font-sans font-semibold tracking-wider">Expected</p>
                                            <div className="bg-[#0e0e20] p-2 rounded text-emerald-400 break-words">{res.expected_output}</div>
                                        </div>
                                    )}
                                </div>

                                {res.error && (
                                    <div className="mt-1 p-2 bg-rose-500/10 rounded border border-rose-500/20">
                                        <p className="text-rose-300 font-mono text-xs whitespace-pre-wrap">{res.error}</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            <style jsx>{`
                .results-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }
                .results-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .results-scrollbar::-webkit-scrollbar-thumb {
                    background: #3a3a5a;
                    border-radius: 3px;
                }
                .results-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #4a4a6a;
                }
            `}</style>
        </div>
    )
}

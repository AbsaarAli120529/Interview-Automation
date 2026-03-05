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
            <div className="flex flex-col items-center justify-center p-8 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
                <p className="text-sm text-gray-600 font-medium">
                    {isSubmitting ? "Submitting and running hidden tests..." : "Running test cases..."}
                </p>
            </div>
        )
    }

    if (error) {
        return (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                <p className="font-bold mb-1">Execution Error</p>
                <p className="font-mono text-xs">{error}</p>
            </div>
        )
    }

    if (!results || results.length === 0) {
        return (
            <div className="p-8 text-center bg-gray-50 rounded-lg border border-dashed border-gray-300 text-gray-400 text-sm italic">
                Run your code to see results here.
            </div>
        )
    }

    return (
        <div className="flex flex-col bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
            <div className="px-4 py-3 border-b flex items-center justify-between bg-gray-50/80">
                <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-gray-900">Test Results</h3>
                    {summary && (
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${summary.passed === summary.total ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                            }`}>
                            {summary.passed} / {summary.total} Passed
                        </span>
                    )}
                </div>

                {submissionStatus && (
                    <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded border ${submissionStatus === 'passed' ? 'bg-green-500 text-white border-green-600' :
                            submissionStatus === 'failed' ? 'bg-red-500 text-white border-red-600' :
                                'bg-yellow-500 text-white border-yellow-600'
                        }`}>
                        {submissionStatus}
                    </span>
                )}
            </div>

            <div className="max-h-60 overflow-y-auto p-2 space-y-2">
                {results.map((res, idx) => (
                    <div key={idx} className={`p-3 rounded-md border text-xs ${res.passed ? 'border-green-100 bg-green-50/30' : 'border-red-100 bg-red-50/30'
                        }`}>
                        <div className="flex items-center justify-between mb-2">
                            <span className="font-bold text-gray-500 uppercase tracking-tighter text-[9px]">Case {idx + 1}</span>
                            <span className={res.passed ? 'text-green-600 font-black' : 'text-red-600 font-black'}>
                                {res.passed ? '✓ PASSED' : '✗ FAILED'}
                            </span>
                        </div>

                        <div className="grid grid-cols-2 gap-4 font-mono">
                            <div>
                                <p className="text-[9px] text-gray-400 mb-0.5 uppercase">Input</p>
                                <div className="bg-gray-100 p-1.5 rounded text-gray-700 truncate">{res.input}</div>
                            </div>
                            <div>
                                <p className="text-[9px] text-gray-400 mb-0.5 uppercase">Output</p>
                                <div className="bg-gray-100 p-1.5 rounded text-gray-700 truncate">{res.actual_output}</div>
                            </div>
                        </div>

                        {!res.passed && !res.error && (
                            <div className="mt-2 text-[9px]">
                                <p className="text-gray-400 uppercase mb-0.5">Expected</p>
                                <div className="text-red-800 font-mono italic">{res.expected_output}</div>
                            </div>
                        )}

                        {res.error && (
                            <div className="mt-2 p-1.5 bg-red-900/5 rounded border border-red-900/10">
                                <p className="text-red-800 font-mono text-[10px] whitespace-pre-wrap">{res.error}</p>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    )
}

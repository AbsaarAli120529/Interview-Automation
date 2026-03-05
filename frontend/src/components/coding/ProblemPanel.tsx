import React from "react"
import { CodingProblem } from "@/lib/api/codingApi"

interface ProblemPanelProps {
    title: string
    difficulty: string
    description: string
    examples: CodingProblem["examples"]
}

export default function ProblemPanel({
    title,
    difficulty,
    description,
    examples
}: ProblemPanelProps) {
    return (
        <div className="flex flex-col h-full bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
                <h2 className="text-xl font-bold text-gray-900">{title}</h2>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${difficulty.toLowerCase() === 'easy' ? 'bg-green-100 text-green-700' :
                        difficulty.toLowerCase() === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                    }`}>
                    {difficulty}
                </span>
            </div>

            <div className="p-6 overflow-y-auto flex-1 space-y-6">
                <div>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-tight mb-2">Description</h3>
                    <div className="prose prose-sm max-w-none text-gray-800 leading-relaxed whitespace-pre-wrap">
                        {description}
                    </div>
                </div>

                {examples && examples.length > 0 && (
                    <div>
                        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-tight mb-3">Example Cases</h3>
                        <div className="space-y-4">
                            {examples.map((ex, idx) => (
                                <div key={idx} className="bg-gray-50 rounded-md p-3 border border-gray-100 text-sm">
                                    <div className="mb-2">
                                        <span className="font-mono font-bold text-gray-600 mr-2 uppercase text-[10px]">Input:</span>
                                        <code className="bg-gray-100 px-1.5 py-0.5 rounded text-gray-900">{ex.input}</code>
                                    </div>
                                    <div>
                                        <span className="font-mono font-bold text-gray-600 mr-2 uppercase text-[10px]">Expected:</span>
                                        <code className="bg-gray-100 px-1.5 py-0.5 rounded text-gray-900">{ex.expected_output}</code>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

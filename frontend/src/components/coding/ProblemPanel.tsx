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
        <div className="flex flex-col h-full bg-[#282828] rounded-lg overflow-hidden border border-[#3e3e42] shadow-xl">
            <div className="px-5 py-3 border-b border-[#3e3e42] flex items-center justify-between bg-[#313131]">
                {/* Title matches LC style (e.g. bold, white/light gray) */}
                <h2 className="text-lg font-semibold text-[#eff1f6]">{title}</h2>
                <span className={`px-2 py-0.5 rounded text-[11px] font-medium tracking-wide ${difficulty.toLowerCase() === 'easy' ? 'text-teal-400 bg-teal-400/10' :
                    difficulty.toLowerCase() === 'medium' ? 'text-yellow-400 bg-yellow-400/10' :
                        'text-red-500 bg-red-500/10'
                    }`}>
                    {difficulty}
                </span>
            </div>

            <div className="p-5 overflow-y-auto flex-1 space-y-6 custom-scrollbar text-[#eff1f6]">
                <div className="prose prose-sm prose-invert max-w-none text-[#bfbpc1] leading-relaxed whitespace-pre-wrap font-[system-ui]">
                    {description}
                </div>

                {examples && examples.length > 0 && (
                    <div className="space-y-4">
                        {examples.map((ex, idx) => (
                            <div key={idx} className="space-y-2">
                                <h3 className="text-sm font-semibold text-[#eff1f6]">Example {idx + 1}:</h3>
                                <div className="bg-[#3e3e42]/50 rounded-lg p-4 border-l-2 border-[#5c5c60] text-sm text-[#bfbfc1] font-mono leading-relaxed">
                                    <div>
                                        <span className="font-bold text-[#eff1f6]">Input: </span>
                                        {ex.input}
                                    </div>
                                    <div>
                                        <span className="font-bold text-[#eff1f6]">Output: </span>
                                        {ex.expected_output}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
            {/* Adding basic custom scrollbar css block for this component's scope */}
            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 8px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #5c5c60;
                    border-radius: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #7a7a7d;
                }
            `}</style>
        </div>
    )
}

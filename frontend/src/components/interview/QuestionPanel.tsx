import { QuestionResponse } from "@/types/api";

interface QuestionPanelProps {
    question: QuestionResponse;
}

const ANSWER_MODE_CONFIG = {
    AUDIO: {
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
            </svg>
        ),
        label: "Audio",
        className: "bg-purple-100 text-purple-800",
    },
    TEXT: {
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
            </svg>
        ),
        label: "Written",
        className: "bg-blue-100 text-blue-800",
    },
    CODE: {
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
            </svg>
        ),
        label: "Code",
        className: "bg-green-100 text-green-800",
    },
};

export default function QuestionPanel({ question }: QuestionPanelProps) {
    const modeConfig = ANSWER_MODE_CONFIG[question.answer_mode] ?? ANSWER_MODE_CONFIG.TEXT;

    return (
        <div className="border rounded-lg shadow-sm bg-white overflow-hidden">
            <div className="bg-gray-50 px-6 py-4 border-b flex flex-wrap gap-2 items-center">
                {question.category && (
                    <span className="bg-orange-100 text-orange-800 text-xs font-semibold px-2.5 py-0.5 rounded">
                        {question.category}
                    </span>
                )}
                {question.difficulty && (
                    <span className="bg-green-100 text-green-800 text-xs font-semibold px-2.5 py-0.5 rounded capitalize">
                        {question.difficulty}
                    </span>
                )}
                <span className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-0.5 rounded ${modeConfig.className}`}>
                    {modeConfig.icon}
                    {modeConfig.label}
                </span>
            </div>
            <div className="p-6">
                <pre className="whitespace-pre-wrap font-sans text-gray-800 text-lg leading-relaxed">
                    {question.question_text || question.prompt}
                </pre>
            </div>
        </div>
    );
}
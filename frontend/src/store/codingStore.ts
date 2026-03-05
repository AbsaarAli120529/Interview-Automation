import { create } from "zustand"
import {
    CodingProblem,
    TestCaseResult,
    runCode,
    submitCode,
    CodeRunResponse,
    CodeSubmitResponse
} from "@/lib/api/codingApi"

interface CodingState {
    problem: CodingProblem | null
    language: string
    code: string
    results: TestCaseResult[]
    resultSummary: { passed: number; total: number } | null
    isRunning: boolean
    isSubmitting: boolean
    isSubmitted: boolean
    submissionStatus: "passed" | "failed" | "error" | null
    error: string | null

    // Actions
    setProblemFromInterview: (question: any) => void
    setLanguage: (lang: string) => void
    setCode: (code: string) => void
    runCurrentCode: () => Promise<void>
    submitCurrentCode: (interviewId?: string, candidateId?: string) => Promise<void>
}

export const useCodingStore = create<CodingState>((set, get) => ({
    problem: null,
    language: "python3",
    code: "",
    results: [],
    resultSummary: null,
    isRunning: false,
    isSubmitting: false,
    isSubmitted: false,
    submissionStatus: null,
    error: null,

    setProblemFromInterview: (question: any) => {
        // Backend returns 'starter_code' as a dict mapping lang -> code
        const problem: CodingProblem = {
            id: question.problem_id,
            title: question.title,
            description: question.description,
            difficulty: question.difficulty || "medium",
            starter_code: question.starter_code || {},
            examples: question.examples || [],
            time_limit_sec: question.time_limit_sec || 900
        }

        const defaultLang = "python3"
        set({
            problem,
            language: defaultLang,
            code: problem.starter_code[defaultLang] || "",
            results: [],
            resultSummary: null,
            isRunning: false,
            isSubmitting: false,
            isSubmitted: false,
            submissionStatus: null,
            error: null,
        })
    },

    setLanguage: (lang: string) => {
        const { problem } = get()
        if (!problem) return
        set({
            language: lang,
            code: problem.starter_code[lang] || ""
        })
    },

    setCode: (code: string) => set({ code }),

    runCurrentCode: async () => {
        const { problem, language, code, isRunning, isSubmitting } = get()
        if (!problem || isRunning || isSubmitting) return

        set({ isRunning: true, error: null })
        try {
            const response: CodeRunResponse = await runCode({
                problem_id: problem.id,
                language,
                source_code: code
            })
            set({
                results: response.results,
                resultSummary: { passed: response.passed, total: response.total },
                isRunning: false
            })
        } catch (err: any) {
            set({ error: err.message || "Failed to run code", isRunning: false })
        }
    },

    submitCurrentCode: async (interviewId?: string, candidateId?: string) => {
        const { problem, language, code, isRunning, isSubmitting, isSubmitted } = get()
        if (!problem || isRunning || isSubmitting || isSubmitted) return

        set({ isSubmitting: true, error: null })
        try {
            const response: CodeSubmitResponse = await submitCode({
                problem_id: problem.id,
                language,
                source_code: code,
                interview_id: interviewId,
                candidate_id: candidateId
            })
            set({
                results: response.results,
                resultSummary: { passed: response.passed, total: response.total },
                isSubmitting: false,
                isSubmitted: true,
                submissionStatus: response.status as "passed" | "failed" | "error"
            })
        } catch (err: any) {
            set({ error: err.message || "Failed to submit code", isSubmitting: false })
        }
    }
}))

export interface CodingProblem {
    id: string
    session_question_id?: string
    title: string
    description: string
    difficulty: string
    starter_code: Record<string, string>
    examples: { input: string; expected_output: string }[]
    time_limit_sec: number
}

export interface TestCaseResult {
    test_case_id: string
    input: string
    expected_output: string
    actual_output: string
    passed: boolean
    error?: string
}

export interface CodeRunResponse {
    passed: number
    total: number
    results: TestCaseResult[]
}

export interface CodeSubmitResponse {
    submission_id: string
    status: string
    passed: number
    total: number
    results: TestCaseResult[]
    state?: string
}

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

export async function runCode(payload: {
    problem_id: string
    session_question_id?: string
    language: string
    source_code: string
    interview_id?: string
    candidate_id?: string
}): Promise<CodeRunResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/candidate/coding/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Failed to run code" }))
        throw new Error(error.detail || "Failed to run code")
    }
    return res.json()
}

export async function submitCode(payload: {
    problem_id: string
    session_question_id?: string
    language: string
    source_code: string
    interview_id?: string
    candidate_id?: string
}): Promise<CodeSubmitResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/candidate/coding/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Failed to submit code" }))
        throw new Error(error.detail || "Failed to submit code")
    }
    return res.json()
}

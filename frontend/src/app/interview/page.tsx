"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useInterviewStore } from "@/store/interviewStore";
import InterviewShell from "@/components/interview/InterviewShell";
import SectionSelector from "@/components/interview/SectionSelector";

export default function InterviewPage() {
    const interviewId = useInterviewStore((s) => s.interviewId);
    const candidateToken = useInterviewStore((s) => s.candidateToken);
    const state = useInterviewStore((s) => s.state);
    const currentSection = useInterviewStore((s) => s.currentSection);
    const terminationReason = useInterviewStore((s) => s.terminationReason);
    const isConnected = useInterviewStore((s) => s.isConnected);
    const error = useInterviewStore((s) => s.error);
    const startInterview = useInterviewStore((s) => s.startInterview);
    const initialize = useInterviewStore((s) => s.initialize);
    const hasStarted = useRef(false);

    const router = useRouter();

    useEffect(() => {
        if (!interviewId || !candidateToken) {
            router.replace("/candidate");
            return;
        }

        if (!isConnected) {
            initialize(interviewId, candidateToken);
            return;
        }

        if (hasStarted.current) return;

        hasStarted.current = true;
        startInterview();
    }, [interviewId, candidateToken, isConnected, startInterview, initialize, router]);

    // Redirect to summary page when interview completes
    useEffect(() => {
        if (state === "COMPLETED") {
            router.push("/summary");
        }
    }, [state, router]);

    if (!interviewId || !candidateToken) {
        return (
            <div className="flex h-screen items-center justify-center text-gray-500">
                Redirecting to dashboard...
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex h-screen items-center justify-center text-red-600 font-bold">
                Error: {error}
            </div>
        );
    }

    if (state === null) {
        return (
            <div className="flex h-screen items-center justify-center text-gray-500">
                Initializing interview...
            </div>
        );
    }

    if (state === "TERMINATED") {
        return (
            <div className="flex flex-col h-screen items-center justify-center text-red-600">
                <h1 className="text-2xl font-bold mb-4">Interview Terminated</h1>
                {terminationReason && <p className="text-lg">{terminationReason}</p>}
            </div>
        );
    }

    // COMPLETED → redirecting; show brief transition screen
    if (state === "COMPLETED") {
        return (
            <div className="flex h-screen items-center justify-center text-gray-500">
                Preparing your results…
            </div>
        );
    }

    if ((state === "IN_PROGRESS" || state === "READY" || state === "SECTION_COMPLETED") && !currentSection) {
        return <SectionSelector />;
    }

    return <InterviewShell />;
}

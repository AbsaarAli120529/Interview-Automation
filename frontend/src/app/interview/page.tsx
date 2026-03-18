"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useInterviewStore } from "@/store/interviewStore";
import { useAuthStore } from "@/store/authStore";
import { fetchActiveInterview } from "@/lib/api/interviews";
import InterviewShell from "@/components/interview/InterviewShell";
import SectionSelector from "@/components/interview/SectionSelector";
import { controlWebSocket } from "@/lib/controlWebSocket";

export default function InterviewPage() {
    const interviewId = useInterviewStore((s) => s.interviewId);
    const candidateToken = useInterviewStore((s) => s.candidateToken);
    const state = useInterviewStore((s) => s.state);
    const currentSection = useInterviewStore((s) => s.currentSection);
    const isLoadingQuestion = useInterviewStore((s) => s.isLoadingQuestion);
    const terminationReason = useInterviewStore((s) => s.terminationReason);
    const isConnected = useInterviewStore((s) => s.isConnected);
    const error = useInterviewStore((s) => s.error);
    const startInterview = useInterviewStore((s) => s.startInterview);
    const initialize = useInterviewStore((s) => s.initialize);
    const terminate = useInterviewStore((s) => s.terminate);
    
    const { isAuthenticated, _hasHydrated } = useAuthStore();
    const [isRecovering, setIsRecovering] = useState(false);
    
    const hasStarted = useRef(false);
    const hasInitializedWS = useRef(false);

    const router = useRouter();

    /** Helper to get JWT from localStorage key 'auth-storage' exactly as candidate/page.tsx does */
    const getJwt = (): string => {
        try {
            const raw = localStorage.getItem('auth-storage');
            return JSON.parse(raw ?? '{}')?.state?.token ?? '';
        } catch {
            return '';
        }
    };

    // ─── 1. Session Recovery useEffect ────────────────────────────
    useEffect(() => {
        if (!_hasHydrated) return; // Wait for authStore rehydration

        const performRecovery = async () => {
            // Case 1: Already have session in store (proceed normally)
            if (interviewId && candidateToken) return;

            // Case 2: No session in store - check authentication
            if (!isAuthenticated) {
                router.push("/login/candidate");
                return;
            }

            // Case 3: Authenticated but store is empty (potential reload case)
            setIsRecovering(true);
            try {
                const session = await fetchActiveInterview();
                if (session && session.status === 'in_progress' && session.session_id) {
                    const jwt = getJwt();
                    // Recover session: Seed the interviewStore
                    initialize(session.session_id, jwt);
                } else {
                    // No active in-progress session found, back to dashboard
                    router.push("/candidate");
                }
            } catch (err) {
                console.error("Session recovery failed:", err);
                router.push("/candidate");
            } finally {
                setIsRecovering(false);
            }
        };

        performRecovery();
    }, [_hasHydrated, isAuthenticated, interviewId, candidateToken, router, initialize]);

    // ─── 2. WebSocket Initialization ───────────────────────────────
    useEffect(() => {
        if (hasInitializedWS.current) return;

        const wsState = controlWebSocket.getReadyState();
        if (wsState === WebSocket.OPEN || wsState === WebSocket.CONNECTING) return;

        if (!interviewId || !candidateToken) return;

        hasInitializedWS.current = true;
        initialize(interviewId, candidateToken);

        return () => {
            // terminate() is handled by beforeunload or navigation, not unmount (Strict Mode)
        };
    }, [interviewId, candidateToken, initialize]);

    // ─── 3. Start Interview Logic ──────────────────────────────────
    useEffect(() => {
        if (!isConnected) return;
        if (hasStarted.current) return;

        hasStarted.current = true;
        startInterview();
    }, [isConnected, startInterview]);

    // ─── 4. Terminal Handling ─────────────────────────────────────
    useEffect(() => {
        const handleUnload = () => terminate();
        window.addEventListener('beforeunload', handleUnload);
        return () => {
            window.removeEventListener('beforeunload', handleUnload);
        };
    }, [terminate]);

    // ─── 5. Redirect on Completion ────────────────────────────────
    useEffect(() => {
        if (state === "COMPLETED") {
            router.push("/summary");
        }
    }, [state, router]);

    // ─── Render ───────────────────────────────────────────────────

    // Recovery Loader
    if (isRecovering) {
        return (
            <div className="flex h-screen items-center justify-center text-gray-500">
                Restoring your session...
            </div>
        );
    }

    // Default redirect if no session and not recovering
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

    if (isLoadingQuestion) {
        return (
            <div className="flex h-screen flex-col items-center justify-center gap-4 bg-gray-50">
                <div className="w-14 h-14 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin" />
                <p className="text-gray-500 font-semibold text-lg">Generating your question...</p>
                <p className="text-gray-400 text-sm">This may take a few seconds</p>
            </div>
        );
    }

    return <InterviewShell />;
}

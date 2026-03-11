"use client";

import { useState, useEffect, useRef } from "react";

interface TimerProps {
    durationSec: number;
    onExpire: () => void;
}

export default function Timer({ durationSec, onExpire }: TimerProps) {
    const [remaining, setRemaining] = useState(durationSec);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const onExpireRef = useRef(onExpire);
    const hasExpiredRef = useRef(false);

    useEffect(() => {
        onExpireRef.current = onExpire;
    }, [onExpire]);

    useEffect(() => {
        setRemaining(durationSec);
        hasExpiredRef.current = false;

        if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }

        intervalRef.current = setInterval(() => {
            setRemaining((prev) => {
                if (prev <= 1) {
                    if (intervalRef.current) {
                        clearInterval(intervalRef.current);
                    }
                    if (!hasExpiredRef.current) {
                        hasExpiredRef.current = true;
                        onExpireRef.current();
                    }
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [durationSec]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    };

    const isLow = remaining <= 60;
    const isCritical = remaining <= 30;

    return (
        <div className={`
            font-mono text-sm font-bold px-3 py-1 rounded-md flex items-center gap-1.5 transition-all duration-300
            ${isCritical
                ? 'text-rose-400 bg-rose-400/10 ring-1 ring-rose-400/20 animate-pulse'
                : isLow
                    ? 'text-amber-400 bg-amber-400/10 ring-1 ring-amber-400/20'
                    : 'text-[#c4c4cc] bg-[#252545]'
            }
        `}>
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {formatTime(remaining)}
        </div>
    );
}

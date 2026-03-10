"use client";

import { useEffect, useRef, useState } from "react";

interface VideoFeedProps {
    onStreamReady?: (stream: MediaStream) => void;
}

export default function VideoFeed({ onStreamReady }: VideoFeedProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isStreaming, setIsStreaming] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const streamRef = useRef<MediaStream | null>(null);

    useEffect(() => {
        const startVideo = async () => {
            try {
                // Request only video for the feed - audio will be handled separately by AnswerPanel
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 640, height: 480, facingMode: "user" },
                    audio: false, // Don't request audio here to avoid conflicts
                });
                
                streamRef.current = stream;
                
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    setIsStreaming(true);
                    setError(null);
                    // Pass stream without audio to avoid conflicts
                    onStreamReady?.(stream);
                }
            } catch (err) {
                const errorMessage = err instanceof Error ? err.message : "Failed to access camera";
                setError(errorMessage);
                setIsStreaming(false);
            }
        };

        startVideo();

        return () => {
            if (streamRef.current) {
                streamRef.current.getTracks().forEach((track) => {
                    if (track.readyState !== "ended") {
                        track.stop();
                    }
                });
                streamRef.current = null;
            }
        };
    }, [onStreamReady]);

    return (
        <div className="relative bg-black rounded-lg overflow-hidden aspect-video">
            {error ? (
                <div className="flex items-center justify-center h-full text-red-500">
                    <p>Camera Error: {error}</p>
                </div>
            ) : (
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                />
            )}
            {isStreaming && (
                <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded text-xs font-semibold flex items-center gap-1">
                    <span className="w-2 h-2 bg-white rounded-full animate-pulse"></span>
                    LIVE
                </div>
            )}
        </div>
    );
}

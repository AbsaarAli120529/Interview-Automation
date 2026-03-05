"use client";

import { useState, useRef, useEffect } from "react";
import { answerWebSocket } from "@/lib/answerWebSocket";

interface AnswerPanelProps {
    mode: "AUDIO" | "CODE" | "TEXT";
    value: string;
    onChange: (value: string) => void;
    questionId: string;
    onVoiceStart?: () => void;
}

export default function AnswerPanel({
    mode,
    value,
    onChange,
    questionId,
    onVoiceStart,
}: AnswerPanelProps) {
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState("");
    const [finalTranscript, setFinalTranscript] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const mediaStreamRef = useRef<MediaStream | null>(null);
    const recorderRef = useRef<MediaRecorder | null>(null);
    const isCleaningUpRef = useRef(false);

    const cleanup = () => {
        if (isCleaningUpRef.current) return; // Prevent double cleanup
        isCleaningUpRef.current = true;

        // Stop recorder first
        if (recorderRef.current) {
            try {
                if (recorderRef.current.state === "recording") {
                    recorderRef.current.stop();
                }
            } catch (e) {
                // Ignore errors if already stopped
            }
            // Clear recorder reference
            recorderRef.current = null;
        }

        // Stop all tracks with proper state checking
        if (mediaStreamRef.current) {
            try {
                const tracks = mediaStreamRef.current.getTracks();
                tracks.forEach((track) => {
                    try {
                        if (track.readyState === "live") {
                            track.stop();
                        }
                    } catch (e) {
                        // Track might already be stopped, ignore
                    }
                });
            } catch (e) {
                // Ignore errors if tracks already stopped
            }
            // Clear stream reference
            mediaStreamRef.current = null;
        }

        // Disconnect WebSocket
        try {
            answerWebSocket.disconnect();
        } catch (e) {
            // Ignore WebSocket disconnect errors
        }

        setIsRecording(false);
        setError(null);
        isCleaningUpRef.current = false;
    };

    useEffect(() => {
        // Cleanup when component unmounts or question changes
        return () => {
            cleanup();
        };
    }, [questionId]); // Re-run cleanup when question changes

    // Sync transcript with value when transcript updates during recording
    useEffect(() => {
        if (transcript && transcript.trim() && isRecording) {
            // Only update if transcript is different from current value
            // This prevents overwriting user edits
            if (transcript !== value) {
                onChange(transcript);
            }
        }
    }, [transcript, isRecording]); // Update when transcript changes during recording

    const startRecording = async () => {
        if (isRecording) {
            console.log("[AnswerPanel] Already recording, ignoring start request");
            return;
        }

        console.log("[AnswerPanel] Starting recording...");

        // Cleanup any existing stream first
        cleanup();

        // Small delay to ensure cleanup is complete
        await new Promise(resolve => setTimeout(resolve, 200));

        try {
            setError(null);
            setTranscript("");
            setFinalTranscript(null);
            console.log("[AnswerPanel] Initialized state, connecting WebSocket...");

            // Step 1: Connect WebSocket first
            let wsReady = false;
            let wsError = false;

            answerWebSocket.connect({
                questionId,
                onOpen: () => {
                    wsReady = true;
                },
                onPartialTranscript: (text) => {
                    // Update transcript state with latest partial text
                    // Azure sends incremental updates, so we use the latest text directly
                    setTranscript(text);
                    // Update the parent value immediately so it shows in the textarea
                    if (text && text.trim()) {
                        onChange(text);
                    } else if (text) {
                        // Even if empty, update to show "Listening..."
                        onChange(text);
                    }
                },
                onFinalTranscript: (text) => {
                    // Final transcript replaces everything
                    setTranscript(text);
                    onChange(text);
                    setFinalTranscript(text);
                },
                onAnswerReady: (transcriptId) => {
                    // transcriptId is the final transcript text
                    onChange(transcriptId);
                    setFinalTranscript(transcriptId);
                    setIsRecording(false);
                },
                onError: (error) => {
                    console.error("[AnswerPanel] WebSocket error:", error);
                    wsError = true;
                    setError("WebSocket connection failed");
                    cleanup();
                },
                onClose: () => {
                    setIsRecording(false);
                },
            });

            // Wait for WebSocket to be ready (with timeout)
            let waitCount = 0;
            while (!wsReady && !wsError && waitCount < 50) {
                await new Promise(resolve => setTimeout(resolve, 100));
                waitCount++;
            }

            if (wsError) {
                throw new Error("WebSocket connection failed");
            }

            if (!wsReady) {
                throw new Error("WebSocket connection timeout");
            }

            // Step 2: Get audio stream after WebSocket is ready
            // Request a fresh audio stream
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 16000, // Match Azure's expected sample rate
                } 
            });
            
            // Verify stream is active
            const audioTracks = stream.getAudioTracks();
            if (audioTracks.length === 0) {
                stream.getTracks().forEach(track => {
                    try {
                        track.stop();
                    } catch (e) {
                        // Ignore
                    }
                });
                throw new Error("Failed to get audio track");
            }

            const audioTrack = audioTracks[0];
            if (audioTrack.readyState !== "live") {
                stream.getTracks().forEach(track => {
                    try {
                        track.stop();
                    } catch (e) {
                        // Ignore
                    }
                });
                throw new Error("Audio track is not live");
            }

            // Store stream reference
            mediaStreamRef.current = stream;

            // Step 3: Create MediaRecorder
            // Verify stream is still valid before creating recorder
            if (!mediaStreamRef.current || mediaStreamRef.current.getAudioTracks().length === 0) {
                throw new Error("Media stream is no longer valid");
            }

            const activeTracks = mediaStreamRef.current.getAudioTracks().filter(t => t.readyState === "live");
            if (activeTracks.length === 0) {
                throw new Error("No active audio tracks available");
            }

            let mimeType = 'audio/webm;codecs=opus';
            
            // Check if the mime type is supported
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                // Try other formats
                if (MediaRecorder.isTypeSupported('audio/webm')) {
                    mimeType = 'audio/webm';
                } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
                    mimeType = 'audio/ogg;codecs=opus';
                } else {
                    mimeType = ''; // Use default
                }
            }

            let recorder: MediaRecorder;
            try {
                recorder = new MediaRecorder(mediaStreamRef.current, mimeType ? { mimeType } : undefined);
                recorderRef.current = recorder;
            } catch (recorderError) {
                console.error("[AnswerPanel] Error creating MediaRecorder:", recorderError);
                // Cleanup stream if recorder creation fails
                if (mediaStreamRef.current) {
                    mediaStreamRef.current.getTracks().forEach(track => {
                        try {
                            track.stop();
                        } catch (e) {
                            // Ignore
                        }
                    });
                    mediaStreamRef.current = null;
                }
                throw new Error(`Failed to create MediaRecorder: ${recorderError}`);
            }

            // Set up recorder event handlers
            recorder.ondataavailable = async (event) => {
                if (event.data && event.data.size > 0) {
                    try {
                        const arrayBuffer = await event.data.arrayBuffer();
                        answerWebSocket.sendAudio(arrayBuffer);
                    } catch (e) {
                        console.error("[AnswerPanel] Error sending audio:", e);
                    }
                }
            };

            recorder.onerror = (event) => {
                console.error("[AnswerPanel] MediaRecorder error:", event);
                setError("Recording error occurred");
                cleanup();
            };

            recorder.onstop = () => {
                console.log("[AnswerPanel] MediaRecorder stopped");
            };

            // Start recording
            try {
                recorder.start(1000); // Send chunks every second
                setIsRecording(true);
                onVoiceStart?.(); // Trigger voice verification
            } catch (startError) {
                console.error("[AnswerPanel] Error starting recorder:", startError);
                cleanup();
                throw new Error(`Failed to start recording: ${startError}`);
            }

        } catch (error) {
            console.error("[AnswerPanel] Error starting recording:", error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to start recording';
            setError(errorMessage);
            console.error("[AnswerPanel] Error details:", {
                message: errorMessage,
                error: error,
                isRecording,
                hasStream: !!mediaStreamRef.current,
                hasRecorder: !!recorderRef.current
            });
            cleanup();
        }
    };

    const stopRecording = () => {
        if (!isRecording) return;
        
        // Stop the recorder
        if (recorderRef.current && recorderRef.current.state !== "inactive") {
            recorderRef.current.stop();
        }
        
        // End the answer on WebSocket
        answerWebSocket.endAnswer();
        
        // Cleanup will happen in onAnswerReady or onClose
    };

    if (mode === "CODE") {
        return (
            <textarea
                className="w-full h-64 p-4 border rounded font-mono text-sm"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder="Write your code here..."
            />
        );
    }

    if (mode === "TEXT") {
        return (
            <textarea
                className="w-full h-48 p-4 border rounded text-sm"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder="Type your answer here..."
            />
        );
    }

    return (
        <div className="flex flex-col gap-4 border p-4 rounded bg-gray-50">
            <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-700">Audio Answer</span>
                <button
                    onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log("[AnswerPanel] Button clicked, isRecording:", isRecording);
                        if (isRecording) {
                            stopRecording();
                        } else {
                            startRecording().catch(err => {
                                console.error("[AnswerPanel] Unhandled error in startRecording:", err);
                            });
                        }
                    }}
                    disabled={!!error}
                    className={`px-4 py-2 rounded text-white font-medium transition-colors ${
                        error 
                            ? "bg-gray-400 cursor-not-allowed" 
                            : isRecording 
                                ? "bg-red-600 hover:bg-red-700 active:bg-red-800" 
                                : "bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
                    }`}
                    type="button"
                >
                    {isRecording ? "Stop Speaking" : "Start Speaking"}
                </button>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 rounded p-2 text-red-600 text-sm">
                    {error}
                </div>
            )}

            <div className="bg-white rounded border">
                {isRecording && (
                    <div className="px-4 pt-3 pb-2 flex items-center gap-2 text-blue-600 border-b">
                        <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></span>
                        <span className="text-sm font-medium">Recording... (Live transcription)</span>
                    </div>
                )}
                <textarea
                    className="w-full min-h-[150px] p-4 border-0 rounded text-sm text-gray-800 resize-y focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={value || transcript || ""}
                    onChange={(e) => {
                        onChange(e.target.value);
                        // Clear transcript state when user manually edits
                        if (e.target.value !== transcript) {
                            setTranscript(e.target.value);
                        }
                    }}
                    placeholder={
                        isRecording 
                            ? "Speak your answer... Live transcription will appear here. You can also type to edit."
                            : "Click 'Start Speaking' to begin recording, or type your answer here..."
                    }
                    disabled={false}
                />
                {!isRecording && finalTranscript && (
                    <div className="px-4 pb-2 text-xs text-green-600">
                        ✓ Final transcript received
                    </div>
                )}
            </div>
        </div>
    );
}

"use client";

import { useState, useRef, useEffect, useCallback } from "react";
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
    const timerRef = useRef<NodeJS.Timeout | null>(null);
    const mediaStreamRef = useRef<MediaStream | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
    const isCleaningUpRef = useRef(false);
    const finalSentencesRef = useRef<string[]>([]);

    // Cleanup function to ensure everything is stopped cleanly
    const cleanup = useCallback(() => {
        if (isCleaningUpRef.current) return; // Prevent double cleanup
        isCleaningUpRef.current = true;

        if (scriptProcessorRef.current) {
            scriptProcessorRef.current.disconnect();
            scriptProcessorRef.current = null;
        }
        if (audioContextRef.current) {
            audioContextRef.current.close().catch(console.error);
            audioContextRef.current = null;
        }
        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach(track => {
                try {
                    track.stop();
                } catch (e) {
                    console.error("[AnswerPanel] Error stopping track:", e);
                }
            });
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
    }, []);

    useEffect(() => {
        // Cleanup when component unmounts or question changes
        return () => {
            cleanup();
        };
    }, [questionId]); // Re-run cleanup when question changes

    // We don't need to sync transcript to value here anymore because we do it directly in the WebSocket callbacks.
    // This prevents the textarea from being overwritten incorrectly.
    useEffect(() => {
        // Keeping this effect empty or removing it, but we can use it for debugging if needed.
    }, [transcript, isRecording]);

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

            // If there's already text in the box, preserve it so STT appends to it
            if (value && value.trim()) {
                finalSentencesRef.current = [value.trim()];
                setTranscript(value.trim());
                setFinalTranscript(value.trim());
            } else {
                finalSentencesRef.current = [];
                setTranscript("");
                setFinalTranscript(null);
            }

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
                    const partialText = text || "";
                    const fullText = [...finalSentencesRef.current, partialText].filter(Boolean).join(" ");
                    setTranscript(fullText);
                    onChange(fullText);
                },
                onFinalTranscript: (text) => {
                    if (!text || !text.trim()) return;

                    const trimmed = text.trim();
                    const currentJoined = finalSentencesRef.current.join(" ");

                    // Prevent the endpoint from duplicating the entire string at the end of the session
                    if (trimmed === currentJoined) return;

                    finalSentencesRef.current.push(trimmed);
                    const fullText = finalSentencesRef.current.join(" ");
                    setTranscript(fullText);
                    onChange(fullText);
                    setFinalTranscript(fullText);
                },
                onAnswerReady: (transcriptId) => {
                    // transcriptId acts as the final transcript content from the backend's compilation for the current recording session.
                    // However, we want to preserve all paragraphs accumulated.
                    // onFinalTranscript already processed this chunk right before this event.
                    const fullText = finalSentencesRef.current.join(" ");
                    onChange(fullText || transcriptId);
                    setFinalTranscript(fullText || transcriptId);
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

            // Step 3: Initialize AudioContext and ScriptProcessor for PCM
            const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
            const context = new AudioContextClass();
            audioContextRef.current = context;

            const source = context.createMediaStreamSource(stream);

            // ScriptProcessor for simple PCM extraction (2048 buffer size)
            // 2048 gives us chunks roughly every 42ms at 48kHz
            const processor = context.createScriptProcessor(2048, 1, 1);
            scriptProcessorRef.current = processor;

            // Target Azure sample rate
            const targetSampleRate = 16000;
            const sourceSampleRate = context.sampleRate;

            processor.onaudioprocess = (e) => {
                // If we aren't supposed to be running, abort
                // In React, stale closures can happen, so we just rely on scriptProcessorRef existing as proof we're active
                if (!scriptProcessorRef.current) return;

                const inputData = e.inputBuffer.getChannelData(0);

                // Downsample Float32Array
                const ratio = sourceSampleRate / targetSampleRate;
                const newLength = Math.round(inputData.length / ratio);
                const resampledData = new Float32Array(newLength);
                for (let i = 0; i < newLength; i++) {
                    resampledData[i] = inputData[Math.round(i * ratio)];
                }

                // Convert Float32Array to Int16Array
                let l = resampledData.length;
                const pcmData = new Int16Array(l);
                while (l--) {
                    const s = Math.max(-1, Math.min(1, resampledData[l]));
                    pcmData[l] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }

                if (pcmData.length > 0) {
                    try {
                        answerWebSocket.sendAudio(pcmData.buffer);
                    } catch (err) {
                        console.error("[AnswerPanel] Error sending PCM chunk:", err);
                    }
                }
            };

            // Connect the pipeline
            source.connect(processor);
            processor.connect(context.destination);

            // Start recording state
            try {
                setIsRecording(true);
                onVoiceStart?.(); // Trigger voice verification
            } catch (startError) {
                console.error("[AnswerPanel] Error starting recording state:", startError);
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
                hasStream: !!mediaStreamRef.current
            });
            cleanup();
        }
    };

    const stopRecording = () => {
        if (!isRecording) return;

        // Cleanly disconnect pipeline
        if (scriptProcessorRef.current) {
            scriptProcessorRef.current.disconnect();
            scriptProcessorRef.current = null;
        }

        // End the answer on WebSocket
        answerWebSocket.endAnswer();

        // Cleanup will happen in onAnswerReady or onClose
    };

    if (mode === "CODE") {
        return (
            <textarea
                className="w-full h-64 p-4 border rounded font-mono text-sm text-gray-900"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder="Write your code here..."
            />
        );
    }

    if (mode === "TEXT") {
        return (
            <textarea
                className="w-full h-48 p-4 border rounded text-sm text-gray-900"
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
                    className={`px-4 py-2 rounded text-white font-medium transition-colors ${error
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
                    value={isRecording ? (transcript || value || "") : (value || transcript || "")}
                    onChange={(e) => {
                        const newValue = e.target.value;
                        onChange(newValue);
                        // When user manually edits during recording, update transcript to match
                        // This allows them to edit the transcribed text
                        if (isRecording) {
                            setTranscript(newValue);
                        }
                    }}
                    placeholder={
                        isRecording
                            ? "Speak your answer... Live transcription will appear here as you speak. You can also type to edit."
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

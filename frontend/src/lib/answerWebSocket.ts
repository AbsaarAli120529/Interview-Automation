import { getWSBaseURL } from "./apiClient";
import { io, Socket } from "socket.io-client";

interface ConnectParams {
    questionId: string;
    onOpen: () => void;
    onPartialTranscript: (text: string) => void;
    onFinalTranscript: (text: string) => void;
    onAnswerReady: (transcriptId: string) => void;
    onError: (error: Event) => void;
    onClose: () => void;
}

class AnswerWebSocket {
    private socket: Socket | null = null;
    private questionId: string | null = null;
    private _audioChunkCount: number = 0;
    
    get ws(): Socket | null {
        return this.socket;
    }

    connect(params: ConnectParams): void {
        const { questionId, onOpen, onPartialTranscript, onFinalTranscript, onAnswerReady, onError, onClose } = params;

        if (this.socket) {
            this.disconnect();
        }

        this.questionId = questionId;
        this._audioChunkCount = 0;

        const wsBase = getWSBaseURL();
        // Convert ws:// to http:// and wss:// to https:// for SocketIO
        const httpBase = wsBase.replace(/^ws/, 'http').replace(/^wss/, 'https');
        const socketUrl = `${httpBase}/answer/ws`;
        
        console.log(`[AnswerWebSocket] Connecting to: ${socketUrl}`);
        
        this.socket = io(socketUrl, {
            transports: ['websocket', 'polling'], // Enable polling fallback
            reconnection: false, // Don't auto-reconnect for answer sessions
        });

        this.socket.on('connect', () => {
            if (this.socket && this.socket.connected && this.questionId) {
                this.socket.emit('START_ANSWER', {
                    type: "START_ANSWER",
                    question_id: this.questionId,
                });
                onOpen();
            }
        });

        this.socket.on('STARTED', () => {
            console.log("[AnswerWebSocket] Transcription started");
        });

        this.socket.on('TRANSCRIPT_PARTIAL', (data: any) => {
            console.log("[AnswerWebSocket] PARTIAL TRANSCRIPT:", data.text);
            onPartialTranscript(data.text || "");
        });

        this.socket.on('TRANSCRIPT_FINAL', (data: any) => {
            console.log("[AnswerWebSocket] FINAL TRANSCRIPT:", data.text);
            onFinalTranscript(data.text || "");
        });

        this.socket.on('ANSWER_READY', (data: any) => {
            console.log("[AnswerWebSocket] ANSWER READY:", data.transcript_id);
            onAnswerReady(data.transcript_id || "");
            this.disconnect();
        });

        this.socket.on('ERROR', (data: any) => {
            console.error("[AnswerWebSocket] Error from server:", data.detail);
            onError(new Error(data.detail || "WebSocket error") as any);
        });

        this.socket.on('connect_error', (error: Error) => {
            console.error("[AnswerWebSocket] SocketIO connection error:", error);
            onError(error as any);
        });

        this.socket.on('disconnect', (reason: string) => {
            console.log(`[AnswerWebSocket] SocketIO disconnected: ${reason}`);
            onClose();
        });
    }

    sendAudio(data: ArrayBuffer): void {
        if (this.socket && this.socket.connected) {
            try {
                // Convert ArrayBuffer to base64 for SocketIO
                const base64 = this.arrayBufferToBase64(data);
                this.socket.emit('audio_data', { data: base64 });
                
                this._audioChunkCount++;
                if (this._audioChunkCount % 10 === 0) {
                    console.log(`[AnswerWebSocket] Sent ${this._audioChunkCount} audio chunks`);
                }
            } catch (error) {
                console.error("[AnswerWebSocket] Error sending audio:", error);
            }
        }
    }

    private arrayBufferToBase64(buffer: ArrayBuffer): string {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    endAnswer(): void {
        if (this.socket && this.socket.connected) {
            try {
                this.socket.emit('END_ANSWER', {
                    type: "END_ANSWER",
                });
            } catch (error) {
                console.error("[AnswerWebSocket] Error ending answer:", error);
            }
        }
    }

    disconnect(): void {
        if (this.socket) {
            try {
                if (this.socket.connected) {
                    this.socket.disconnect();
                }
            } catch (error) {
                // Ignore errors during disconnect
            }
            this.socket = null;
        }
        this.questionId = null;
    }
}

export const answerWebSocket = new AnswerWebSocket();

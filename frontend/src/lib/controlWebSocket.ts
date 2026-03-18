import { getWSBaseURL } from "./apiClient";
import { io, Socket } from "socket.io-client";

interface ConnectParams {
    interviewId: string;
    candidateToken: string;
    onOpen: () => void;
    onTerminate: (reason: string) => void;
    onError: (error: Event) => void;
    onClose: (event: CloseEvent) => void;
}

class ControlWebSocket {
    private socket: Socket | null = null;
    private heartbeatIntervalId: ReturnType<typeof setInterval> | null = null;
    private heartbeatIntervalSec: number = 10;

    connect(params: ConnectParams): void {
        if (this.socket && this.socket.connected) {
            console.warn('[controlWebSocket] Already connected. Skipping duplicate connect.');
            return;
        }

        if (this.socket) {
            this.disconnect();
        }

        const { interviewId, candidateToken, onOpen, onTerminate, onError, onClose } = params;

        const wsBase = getWSBaseURL();
        // Convert ws:// to http:// and wss:// to https:// for SocketIO
        const httpBase = wsBase.replace(/^ws/, 'http').replace(/^wss/, 'https');
        const socketUrl = `${httpBase}/proctoring/ws`;
        
        console.log(`[ControlWebSocket] Connecting to: ${socketUrl}`);
        
        try {
            this.socket = io(socketUrl, {
                transports: ['websocket', 'polling'], // Enable polling fallback
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000,
            });

            this.socket.on('connect', () => {
                console.log("[ControlWebSocket] SocketIO connected, sending HANDSHAKE");
                if (this.socket && this.socket.connected) {
                    this.socket.emit('HANDSHAKE', {
                        type: "HANDSHAKE",
                        interview_id: interviewId,
                        candidate_token: candidateToken,
                    });
                }
            });

            this.socket.on('HANDSHAKE_ACK', (data: any) => {
                this.heartbeatIntervalSec = data.heartbeat_interval_sec || 10;
                this.startHeartbeat();
                console.log("[ControlWebSocket] HANDSHAKE_ACK received, connection established");
                onOpen();
            });

            this.socket.on('HEARTBEAT_ACK', () => {
                // Heartbeat acknowledged, do nothing
            });

            this.socket.on('TERMINATE', (data: any) => {
                this.stopHeartbeat();
                const reason = data?.payload?.reason || data?.reason || "Unknown reason";
                console.log("[ControlWebSocket] TERMINATE received:", reason);
                onTerminate(reason);
                this.disconnect();
            });

            this.socket.on('ERROR', (data: any) => {
                console.error("[ControlWebSocket] Error from server:", data.detail);
                const error = new Error(data.detail || "WebSocket error");
                onError(error as any);
            });

            this.socket.on('connect_error', (error: Error) => {
                console.error("[ControlWebSocket] SocketIO connection error:", error);
                onError(error as any);
            });

            this.socket.on('disconnect', (reason: string) => {
                console.log(`[ControlWebSocket] SocketIO disconnected: ${reason}`);
                this.stopHeartbeat();
                // Create a CloseEvent-like object for compatibility
                const closeEvent = {
                    code: 1000,
                    reason: reason || 'none',
                    wasClean: reason === 'io client disconnect'
                } as CloseEvent;
                onClose(closeEvent);
            });

        } catch (error) {
            console.error("[ControlWebSocket] Failed to create SocketIO connection:", error);
            onError(error as Event);
        }
    }

    disconnect(): void {
        if (this.socket) {
            this.stopHeartbeat();
            this.socket.disconnect();
            this.socket = null;
        }
    }

    private startHeartbeat(): void {
        this.stopHeartbeat();
        this.heartbeatIntervalId = setInterval(() => {
            if (this.socket && this.socket.connected) {
                this.socket.emit('HEARTBEAT', { type: "HEARTBEAT" });
            }
        }, this.heartbeatIntervalSec * 1000);
    }

    private stopHeartbeat(): void {
        if (this.heartbeatIntervalId) {
            clearInterval(this.heartbeatIntervalId);
            this.heartbeatIntervalId = null;
        }
    }

    getReadyState(): number {
        if (!this.socket) return 3; // CLOSED
        if (this.socket.connected) return 1; // OPEN
        if (this.socket.disconnected) return 3; // CLOSED
        return 0; // CONNECTING
    }
}

export const controlWebSocket = new ControlWebSocket();

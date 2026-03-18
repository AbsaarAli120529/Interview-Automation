import { io, Socket } from "socket.io-client";

interface ConnectParams {
    onOpen: () => void;
    onError: (error: Event) => void;
    onClose: () => void;
}

class MediaWebSocket {
    private socket: Socket | null = null;
    private reconnectAttempts: number = 0;
    private maxReconnectAttempts: number = 3;
    private manualClose: boolean = false;
    private connectParams: ConnectParams | null = null;

    connect(params: ConnectParams): void {
        if (this.socket) {
            this.disconnect();
        }

        this.connectParams = params;
        this.reconnectAttempts = 0;
        this.manualClose = false;

        this.establishConnection();
    }

    private establishConnection(): void {
        if (!this.connectParams) {
            return;
        }

        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";
        // Convert http:// to ws:// and https:// to wss://, then back to http/https for SocketIO
        const httpUrl = baseUrl
            .replace(/^wss:/, "https:")
            .replace(/^ws:/, "http:");

        const socketUrl = `${httpUrl}/proctoring/media/ws`;

        this.socket = io(socketUrl, {
            transports: ['websocket', 'polling'], // Enable polling fallback
            reconnection: !this.manualClose && this.reconnectAttempts < this.maxReconnectAttempts,
            reconnectionAttempts: this.maxReconnectAttempts,
            reconnectionDelay: 1000,
        });

        this.socket.on('connect', () => {
            this.reconnectAttempts = 0;
            this.connectParams?.onOpen();
        });

        this.socket.on('connect_error', (error: Error) => {
            this.connectParams?.onError(error as any);
        });

        this.socket.on('disconnect', (reason: string) => {
            if (!this.manualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                setTimeout(() => {
                    this.establishConnection();
                }, 1000);
            } else {
                this.connectParams?.onClose();
            }
        });
    }

    send(data: ArrayBuffer): void {
        if (this.socket && this.socket.connected) {
            // Convert ArrayBuffer to base64 for SocketIO
            const base64 = this.arrayBufferToBase64(data);
            this.socket.emit('media_data', { data: base64 });
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

    disconnect(): void {
        this.manualClose = true;
        this.reconnectAttempts = 0;
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
    }
}

export const mediaWebSocket = new MediaWebSocket();

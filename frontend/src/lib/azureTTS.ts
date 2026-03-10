/**
 * Azure Text-to-Speech Service
 * Speaks questions aloud using Azure Cognitive Services
 */

interface TTSOptions {
    voice?: string;
    rate?: string;
    pitch?: string;
}

class AzureTTSService {
    private speechKey: string | null = null;
    private speechRegion: string | null = null;
    private audioContext: AudioContext | null = null;

    constructor() {
        if (typeof window !== "undefined") {
            this.speechKey = process.env.NEXT_PUBLIC_AZURE_SPEECH_KEY || null;
            this.speechRegion = process.env.NEXT_PUBLIC_AZURE_SPEECH_REGION || "eastus";
            this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        }
    }

    async speak(text: string, options: TTSOptions = {}): Promise<void> {
        if (!this.speechKey) {
            // Fallback to browser TTS if Azure key not available
            return this.fallbackTTS(text);
        }

        try {
            const token = await this.getToken();
            const voice = options.voice || "en-US-JennyNeural";
            const rate = options.rate || "medium";
            const pitch = options.pitch || "medium";

            const ssml = `
                <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                    <voice name="${voice}">
                        <prosody rate="${rate}" pitch="${pitch}">
                            ${text}
                        </prosody>
                    </voice>
                </speak>
            `;

            const response = await fetch(
                `https://${this.speechRegion}.tts.speech.microsoft.com/cognitiveservices/v1`,
                {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/ssml+xml",
                        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
                    },
                    body: ssml,
                }
            );

            if (!response.ok) {
                throw new Error(`TTS request failed: ${response.statusText}`);
            }

            const audioData = await response.arrayBuffer();
            await this.playAudio(audioData);
        } catch (error) {
            console.error("Azure TTS error:", error);
            // Fallback to browser TTS
            return this.fallbackTTS(text);
        }
    }

    private async getToken(): Promise<string> {
        const response = await fetch(
            `https://${this.speechRegion}.api.cognitive.microsoft.com/sts/v1.0/issueToken`,
            {
                method: "POST",
                headers: {
                    "Ocp-Apim-Subscription-Key": this.speechKey!,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            }
        );

        if (!response.ok) {
            throw new Error("Failed to get Azure TTS token");
        }

        return await response.text();
    }

    private async playAudio(audioData: ArrayBuffer): Promise<void> {
        if (!this.audioContext) return;

        const audioBuffer = await this.audioContext.decodeAudioData(audioData);
        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.audioContext.destination);

        return new Promise((resolve) => {
            source.onended = () => resolve();
            source.start(0);
        });
    }

    private fallbackTTS(text: string): Promise<void> {
        return new Promise((resolve, reject) => {
            if ("speechSynthesis" in window) {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = "en-US";
                utterance.rate = 1.0;
                utterance.pitch = 1.0;
                utterance.onend = () => resolve();
                utterance.onerror = (e) => reject(e);
                window.speechSynthesis.speak(utterance);
            } else {
                reject(new Error("Text-to-speech not supported"));
            }
        });
    }

    stop(): void {
        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel();
        }
    }
}

export const azureTTS = new AzureTTSService();

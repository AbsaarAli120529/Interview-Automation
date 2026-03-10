/**
 * Typedefs for the ImageCapture API
 * @see https://developer.mozilla.org/en-US/docs/Web/API/ImageCapture
 */

interface ImageCapture {
    readonly track: MediaStreamTrack;
    grabFrame(): Promise<ImageBitmap>;
    takePhoto(photoSettings?: any): Promise<Blob>;
}

declare var ImageCapture: {
    prototype: ImageCapture;
    new(videoTrack: MediaStreamTrack): ImageCapture;
};

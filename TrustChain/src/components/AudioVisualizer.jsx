import useAudioVisualizer from "../hooks/useAudioVisualizer";

export default function AudioVisualizer({ isScanning }) {
  const { canvasRef, error } = useAudioVisualizer(isScanning);

  return (
    <div className="audio-visualizer">
      <canvas
        ref={canvasRef}
        className="visualizer-canvas"
      />

      {error && (
        <div className="visualizer-error">
          마이크 권한이 필요합니다.
        </div>
      )}
    </div>
  );
}
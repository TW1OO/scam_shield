import { useState } from "react";
import AudioVisualizer from "./AudioVisualizer";
import useSpeechRecognition from "../hooks/useSpeechRecognition";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

export default function MediaGuard({
    setShowBottomBar,
    setAnalysisResult,
    openBottomSheet,
}) {
    const { text, start, stop } = useSpeechRecognition();

    const [isScanning, setIsScanning] = useState(false);
    const [risk, setRisk] = useState(null);
    const [audioFile, setAudioFile] = useState(null);
    const [fileName, setFileName] = useState("");
    const [analysisMode, setAnalysisMode] = useState(null); // "record" 또는 "file"
    const [loading, setLoading] = useState(false);

    const startScan = () => {
        if (isScanning) return;
        setAnalysisMode("record");
        setRisk(null);
        start();
        setIsScanning(true);
    };

    const stopScan = () => {
        stop();
        setIsScanning(false);
        // 분석은 "AI 분석 시작" 버튼에서 진행 (기존 흐름 유지)
    };

    const handleAudioFile = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setAudioFile(file);
        setFileName(file.name);
        setAnalysisMode("file");
    };

    // 백엔드 응답 -> 기존 컴포넌트가 기대하는 형식으로 변환
    const mapBackendResponse = (data) => ({
        riskPercentage: data.probability,
        title: `${data.risk_level} 위험도 감지`,
        description: data.reasons?.[0] ?? "",
        detections: data.detected_patterns.map((pattern, i) => ({
            title: pattern,
            status: data.risk_level,
            description: data.reasons?.[i] ?? "",
        })),
        recommendation: data.recommendation,
    });

    const analyzeTranscribedText = async (content) => {
        const response = await fetch(`${API_BASE}/chat/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                messages: [{ sender: "unknown", content }],
            }),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || "분석 요청 실패");
        }

        return await response.json();
    };

    const analyzeAudio = async () => {
        setLoading(true);

        try {
            if (analysisMode === "record") {
                if (!text.trim()) {
                    alert("녹음된 음성이 없습니다.");
                    return;
                }

                const backendResult = await analyzeTranscribedText(text);
                const parsed = mapBackendResponse(backendResult);

                setRisk(parsed.riskPercentage);
                setAnalysisResult(parsed);
                setShowBottomBar(true);
                openBottomSheet();
                return;
            }

            if (analysisMode === "file") {
                alert("음성 파일 분석은 아직 백엔드에서 지원하지 않습니다. (텍스트 변환 기능 필요)");
                return;
            }

            alert("먼저 녹음 또는 파일을 선택하세요.");

        } catch (e) {
            console.error(e);
            alert(e.message || "AI 분석 실패");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="pane">
            <div className="glass-card">
                <div className="card-label">
                    Real-time Call & Video Media Guard
                </div>

                <div className="scan-wrap">
                    <div className={isScanning ? "scan-circle active" : "scan-circle"}>
                        <div className="scan-ring"></div>
                        <div className="scan-center">🎙</div>
                    </div>

                    <div className="scan-title">AI Voice Protection</div>

                    <div className="scan-text">
                        {isScanning
                            ? "실시간 음성을 분석 중입니다."
                            : "음성을 녹음하거나 파일을 업로드하세요."}
                    </div>

                    <div className="scan-sub">
                        {analysisMode === "record" &&
                            (isScanning ? "실시간 녹음 중..." : "녹음 완료")}
                        {analysisMode === "file" && `선택된 파일 : ${fileName}`}
                        {!analysisMode && "녹음 또는 음성 파일을 선택하세요."}
                    </div>

                    {isScanning && (
                        <>
                            <AudioVisualizer isScanning={isScanning} />
                            <div
                                style={{
                                    marginTop: 20,
                                    fontSize: 14,
                                    color: "#666",
                                    whiteSpace: "pre-wrap",
                                }}
                            >
                                {text}
                            </div>
                        </>
                    )}
                </div>

                <div className="media-button-group">
                    <button
                        className="action-btn"
                        onClick={isScanning ? stopScan : startScan}
                    >
                        {isScanning ? "⏹ 실시간 음성 녹음 종료" : "🎙 실시간 음성 녹음 시작"}
                    </button>

                    <label className="upload-btn">
                        <span>📁 음성 파일 선택</span>
                        <input
                            type="file"
                            accept=".wav,.mp3,.m4a,audio/*"
                            hidden
                            onChange={handleAudioFile}
                        />
                    </label>

                    <button
                        className="primary-btn"
                        onClick={analyzeAudio}
                        disabled={loading}
                    >
                        {loading ? "분석 중..." : "🤖 AI 분석 시작"}
                    </button>

                    {loading && (
                        <div className="loading-wrap">
                            <div className="loading-bar"></div>
                            <div style={{ marginTop: 10, color: "#666" }}>
                                AI가 음성을 분석 중입니다...
                            </div>
                        </div>
                    )}
                </div>

                {fileName && (
                    <div style={{ marginTop: 15, color: "#666", fontSize: 14 }}>
                        선택된 파일 : {fileName}
                    </div>
                )}
            </div>

            {risk !== null && (
                <div className="tab-result-card">
                    <div className="tab-result-top">
                        <span>Media Analysis Summary</span>
                        <span style={{ color: risk >= 80 ? "#D93025" : "#1B8A4C" }}>
                            {risk}%
                        </span>
                    </div>

                    <div className="risk-bar-bg">
                        <div className="risk-bar-fill" style={{ width: `${risk}%` }} />
                    </div>

                    <div>
                        {risk >= 80
                            ? "AI가 피싱 위험을 감지했습니다."
                            : "현재까지 안전한 통화입니다."}
                    </div>
                </div>
            )}
        </div>
    );
}
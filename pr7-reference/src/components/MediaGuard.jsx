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
    const [analysisMode, setAnalysisMode] = useState(null);
    const [loading, setLoading] = useState(false);

    // AI 분석 버튼 표시 여부
    const canAnalyze =
        (analysisMode === "record" &&
            text.trim().length > 0 &&
            !isScanning) ||
        (analysisMode === "file" &&
            audioFile !== null);

    const startScan = () => {

        if (isScanning) return;

        setRisk(null);

        setAnalysisMode("record");

        start();

        setIsScanning(true);

    };

    const stopScan = () => {

        stop();

        setIsScanning(false);

    };

    const handleAudioFile = (e) => {

        const file = e.target.files[0];

        if (!file) return;

        setAudioFile(file);

        setFileName(file.name);

        setAnalysisMode("file");

    };

    const removeAudioFile = () => {

        setAudioFile(null);

        setFileName("");

        setAnalysisMode(null);

    };

    // 백엔드 결과 변환
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

            headers: {

                "Content-Type": "application/json",

            },

            body: JSON.stringify({

                messages: [

                    {

                        sender: "unknown",

                        content,

                    },

                ],

            }),

        });

        if (!response.ok) {

            const err = await response.json().catch(() => ({}));

            throw new Error(err.detail || "분석 요청 실패");

        }

        return await response.json();

    };

    const analyzeAudio = async () => {

        if (!canAnalyze) return;

        setLoading(true);

        try {

            if (analysisMode === "record") {

                const backendResult =
                    await analyzeTranscribedText(text);

                const parsed =
                    mapBackendResponse(backendResult);

                setRisk(parsed.riskPercentage);

                setAnalysisResult(parsed);

                setShowBottomBar(true);

                openBottomSheet();

                return;

            }

            if (analysisMode === "file") {

                alert("음성 파일 분석은 아직 지원되지 않습니다.");

                return;

            }

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

                    <div className="scan-center">
                        🎙
                    </div>

                </div>

                <div className="scan-title">
                    AI Voice Protection
                </div>

                <div className="scan-text">
                    {isScanning
                        ? "실시간 음성을 분석 중입니다."
                        : "음성을 녹음하거나 파일을 업로드하세요."}
                </div>

                <div className="scan-sub">

                    {analysisMode === "record" &&
                        (isScanning
                            ? "실시간 녹음 중..."
                            : "녹음 완료")}

                    {analysisMode === "file" &&
                        `선택된 파일 : ${fileName}`}

                    {!analysisMode &&
                        "녹음 또는 음성 파일을 선택하세요."}

                </div>

                {isScanning && (
                    <>
                        <AudioVisualizer
                            isScanning={isScanning}
                        />

                        <div
                            style={{
                                marginTop:20,
                                fontSize:14,
                                color:"#666",
                                whiteSpace:"pre-wrap",
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

                    {isScanning
                        ? "⏹ 실시간 음성 녹음 종료"
                        : "🎙 실시간 음성 녹음 시작"}

                </button>

                <label className="upload-btn">

                    📁 음성 파일 선택

                    <input
                        type="file"
                        accept=".wav,.mp3,.m4a,audio/*"
                        hidden
                        onChange={handleAudioFile}
                    />

                </label>

                {fileName && (

                    <div className="selected-file">

                        <span>
                            📄 {fileName}
                        </span>

                        <button
                            className="remove-btn"
                            onClick={removeAudioFile}
                        >
                            제거
                        </button>

                    </div>

                )}

                {/* 분석 가능한 상태일 때만 버튼 표시 */}
                {canAnalyze && (

                    <button
                        className="primary-btn fade-up"
                        onClick={analyzeAudio}
                        disabled={loading}
                    >

                        {loading
                            ? "AI 분석 중..."
                            : "🤖 AI 분석 시작"}

                    </button>

                )}

                {loading && (

                    <div className="loading-wrap">

                        <div className="loading-bar"></div>

                        <div
                            style={{
                                marginTop:10,
                                color:"#666",
                            }}
                        >
                            AI가 음성을 분석 중입니다...
                        </div>

                    </div>

                )}

            </div>
                        {risk !== null && (

                <div className="tab-result-card fade-up">

                    <div className="tab-result-top">

                        <span>
                            Media Analysis Summary
                        </span>

                        <span
                            style={{
                                color:
                                    risk >= 80
                                        ? "#DC2626"
                                        : risk >= 50
                                        ? "#F59E0B"
                                        : "#16A34A",
                                fontWeight:700,
                            }}
                        >
                            {risk}%
                        </span>

                    </div>

                    <div className="risk-bar-bg">

                        <div
                            className="risk-bar-fill"
                            style={{
                                width: `${risk}%`,
                            }}
                        />

                    </div>

                    <div className="risk-message">

                        {risk >= 80 && (
                            <>
                                🚨 AI가 높은 위험의 보이스피싱 가능성을 감지했습니다.
                            </>
                        )}

                        {risk >= 50 && risk < 80 && (
                            <>
                                ⚠️ 주의가 필요한 통화입니다.
                            </>
                        )}

                        {risk < 50 && (
                            <>
                                ✅ 현재까지는 위험도가 낮습니다.
                            </>
                        )}

                    </div>

                </div>

            )}

        </div>

    </div>

);
}
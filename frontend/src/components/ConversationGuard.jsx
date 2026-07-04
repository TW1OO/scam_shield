import { useState } from "react";
import { imageToBase64 } from "../utils/imageToBase64";

const API_BASE = import.meta.env.VITE_API_BASE_URL; // .env에 추가 필요

export default function ConversationGuard({
    setShowBottomBar,
    setAnalysisResult,
    openBottomSheet,
}) {

    const [mode, setMode] = useState("text");
    const [text, setText] = useState("");
    const [image, setImage] = useState(null);
    const [preview, setPreview] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleFile = (file) => {
        if (!file) return;
        setImage(file);
        setPreview(URL.createObjectURL(file));
    };

    const removeImage = () => {
        setImage(null);
        setPreview(null);
    };

    const canAnalyze = () => {
        if (mode === "text") {
            return text.trim().length >= 5;
        }
        return image !== null;
    };

    // 백엔드 응답을 기존 컴포넌트가 기대하는 형식으로 변환
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

    const analyzeText = async () => {
        const response = await fetch(`${API_BASE}/chat/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                messages: [{ sender: "unknown", content: text }],
            }),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || "분석 요청 실패");
        }

        return await response.json();
    };

    const runAnalysis = async () => {
        setLoading(true);
        try {
            if (mode === "image") {
                alert("이미지 분석은 아직 백엔드에서 지원하지 않습니다.");
                return;
            }

            const backendResult = await analyzeText();
            const parsed = mapBackendResponse(backendResult);

            setAnalysisResult(parsed);
            setShowBottomBar(true);
            openBottomSheet();

        } catch (err) {
            console.error(err);
            alert(err.message || "분석 요청 실패");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="pane">
            <div className="card">
                <div className="card-label">
                    Conversation Text Context Guard
                </div>

                <div className="input-selector">
                    <button
                        className={mode === "text" ? "selector-btn active" : "selector-btn"}
                        onClick={() => setMode("text")}
                    >
                        텍스트 입력
                    </button>
                    <button
                        className={mode === "image" ? "selector-btn active" : "selector-btn"}
                        onClick={() => setMode("image")}
                    >
                        캡처 업로드
                    </button>
                </div>

                {mode === "text" && (
                    <>
                        <textarea
                            className="text-input-area"
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            placeholder="의심되는 대화를 붙여넣으세요."
                        />
                        <div className="text-input-counter">
                            {text.length} / 1000
                        </div>
                    </>
                )}

                {mode === "image" && (
                    <>
                        {!preview && (
                            <label className="upload-zone">
                                <input
                                    type="file"
                                    accept="image/*"
                                    hidden
                                    onChange={(e) => handleFile(e.target.files[0])}
                                />
                                이미지 선택
                            </label>
                        )}
                        {preview && (
                            <div className="preview-wrap">
                                <img src={preview} alt="" className="preview-image" />
                                <button className="remove-btn" onClick={removeImage}>
                                    제거
                                </button>
                            </div>
                        )}
                    </>
                )}

                <button
                    className="primary-btn"
                    disabled={!canAnalyze() || loading}
                    onClick={runAnalysis}
                >
                    {loading ? "AI 분석 중..." : "AI 문맥 분석"}
                </button>
            </div>
        </div>
    );
}
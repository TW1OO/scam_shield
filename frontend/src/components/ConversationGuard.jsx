import { useState } from "react";

const MAX_IMAGES = 10;

export default function ConversationGuard({
    setShowBottomBar,
    setAnalysisResult,
    openBottomSheet,
}) {

    const [mode, setMode] = useState("text");
    const [text, setText] = useState("");
    const [images, setImages] = useState([]);
    const [previews, setPreviews] = useState([]);
    const [loading, setLoading] = useState(false);

    const changeMode = (newMode) => {
        setMode(newMode);
        setText("");
        setImages([]);
        setPreviews([]);
    };

    const handleFile = (e) => {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        const remain = MAX_IMAGES - images.length;
        const selected = files.slice(0, remain);

        setImages((prev) => [...prev, ...selected]);
        setPreviews((prev) => [
            ...prev,
            ...selected.map((file) => URL.createObjectURL(file)),
        ]);
    };

    const removeImage = (index) => {
        setImages((prev) => prev.filter((_, i) => i !== index));
        setPreviews((prev) => prev.filter((_, i) => i !== index));
    };

    const clearImages = () => {
        setImages([]);
        setPreviews([]);
    };

    const canAnalyze = () => {
        if (mode === "text") {
            return text.trim().length >= 5;
        }
        return images.length > 0;
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
        const response = await fetch("/api/chat/analyze", {
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

    const analyzeImage = async () => {
        const formData = new FormData();
        images.forEach((image) => formData.append("files", image));

        const response = await fetch("/api/chat/analyze-image", {
            method: "POST",
            body: formData,
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
            const backendResult =
                mode === "image" ? await analyzeImage() : await analyzeText();
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
                        onClick={() => changeMode("text")}
                    >
                        텍스트 입력
                    </button>
                    <button
                        className={mode === "image" ? "selector-btn active" : "selector-btn"}
                        onClick={() => changeMode("image")}
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
                        {previews.length > 0 && (
                            <div className="preview-grid">
                                {previews.map((img, index) => (
                                    <div className="preview-item" key={index}>
                                        <img src={img} alt="" className="preview-thumb" />
                                        <button
                                            className="preview-remove"
                                            onClick={() => removeImage(index)}
                                        >
                                            ✕
                                        </button>
                                    </div>
                                ))}

                                {images.length < MAX_IMAGES && (
                                    <label className="image-add-btn">
                                        <input
                                            type="file"
                                            accept="image/*"
                                            multiple
                                            hidden
                                            onChange={handleFile}
                                        />
                                        <div className="image-add-content">
                                            <div className="plus-icon">＋</div>
                                            <div>추가</div>
                                        </div>
                                    </label>
                                )}
                            </div>
                        )}

                        {previews.length === 0 && (
                            <label className="image-add-btn large">
                                <input
                                    type="file"
                                    accept="image/*"
                                    multiple
                                    hidden
                                    onChange={handleFile}
                                />
                                <div className="image-add-content">
                                    <div className="plus-icon">＋</div>
                                    <div>이미지 선택</div>
                                </div>
                            </label>
                        )}

                        {images.length > 0 && (
                            <button className="remove-btn" onClick={clearImages}>
                                🗑 전체 삭제
                            </button>
                        )}
                    </>
                )}

                <button
                    className={mode === "image" ? "primary-btn primary-btn--image" : "primary-btn"}
                    disabled={!canAnalyze() || loading}
                    onClick={runAnalysis}
                >
                    {loading ? "AI 분석 중..." : "AI 문맥 분석"}
                </button>
            </div>
        </div>
    );
}

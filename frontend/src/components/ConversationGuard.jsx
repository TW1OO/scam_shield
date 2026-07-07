import { useState } from "react";

const MAX_IMAGES = 10;
const API_BASE = import.meta.env.VITE_API_BASE_URL;

export default function ConversationGuard({
    setShowBottomBar,
    setAnalysisResult,
    openBottomSheet,
}) {

    const [mode, setMode] = useState("text");
    const [messages, setMessages] = useState([{ sender: "", content: "" }]);
    const [images, setImages] = useState([]);
    const [previews, setPreviews] = useState([]);
    const [loading, setLoading] = useState(false);

    const changeMode = (newMode) => {
        setMode(newMode);
        setMessages([{ sender: "", content: "" }]);
        setImages([]);
        setPreviews([]);
    };

    const updateMessage = (index, field, value) => {
        setMessages((prev) =>
            prev.map((m, i) => (i === index ? { ...m, [field]: value } : m))
        );
    };

    const addMessageRow = () => {
        setMessages((prev) => [...prev, { sender: "", content: "" }]);
    };

    const removeMessageRow = (index) => {
        if (messages.length <= 1) {
            alert("입력 창이 하나만 남은 경우에는 삭제할 수 없습니다.");
            return;
        }
        setMessages((prev) => prev.filter((_, i) => i !== index));
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
            return messages.some((m) => m.content.trim().length > 0);
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
        const payload = messages
            .filter((m) => m.content.trim().length > 0)
            .map((m) => ({
                sender: m.sender.trim() || "unknown",
                content: m.content.trim(),
            }));

        const response = await fetch(`${API_BASE}/chat/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ messages: payload }),
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

        const response = await fetch(`${API_BASE}/chat/analyze-image`, {
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
                    <div className="message-list">
                        {messages.map((m, index) => (
                            <div className="message-row" key={index}>
                                <input
                                    className="message-name"
                                    type="text"
                                    value={m.sender}
                                    onChange={(e) => updateMessage(index, "sender", e.target.value)}
                                    placeholder="이름"
                                />
                                <input
                                    className="message-content"
                                    type="text"
                                    value={m.content}
                                    onChange={(e) => updateMessage(index, "content", e.target.value)}
                                    placeholder="내용"
                                />
                                <button
                                    className="message-remove"
                                    onClick={() => removeMessageRow(index)}
                                >
                                    ✕
                                </button>
                            </div>
                        ))}

                        <button className="message-add-btn" onClick={addMessageRow}>
                            ＋ 메시지 추가
                        </button>
                    </div>
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
                    className={
                        mode === "image"
                            ? "primary-btn primary-btn--image"
                            : "primary-btn primary-btn--text"
                    }
                    disabled={!canAnalyze() || loading}
                    onClick={runAnalysis}
                >
                    {loading ? "AI 분석 중..." : "AI 문맥 분석"}
                </button>
            </div>
        </div>
    );
}

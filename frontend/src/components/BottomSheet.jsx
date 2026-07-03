export default function BottomSheet({ open, onClose, result }) {
  if (!open) return null;

  const risk = result?.riskPercentage ?? 0;
  const detections = result?.detections ?? [];

  return (
    <div className="sheet-overlay" onClick={onClose}>
      <div className="sheet mobile-sheet" onClick={(e) => e.stopPropagation()}>

        {/* 경고 */}
        <div className="warning-banner">
          🛡 AI 분석 완료
        </div>

        {/* 헤더 */}
        <div className="sheet-handle"></div>

        <div className="result-header">

            <div className="result-icon">

                🛡

            </div>

            <h2>

                AI 분석 결과

            </h2>

            <p>

                실시간 금융사기 탐지 완료

            </p>

        </div>

        {/* 위험도 */}
        <div className="risk-card">

          <div className="risk-circle">

              <div className="risk-inner">

                  <span>

                      {risk}%

                  </span>

              </div>

          </div>

          <h3>

              {
                  risk>=80
                  ?"매우 위험"

                  :risk>=50
                  ?"주의"

                  :"안전"
              }

          </h3>

          <div className="risk-bar">

              <div

              className="risk-fill"

              style={{

                  width:`${risk}%`

              }}

              />

          </div>

      </div>
        
        {/* AI 요약 */}
        <div className="summary-card">

            <h3>

                AI 요약

            </h3>

            <p>

                {result?.description}

            </p>

        </div>

        {/* 태그 */}
        <div className="tag-row">
          <span>페이스 스왑</span>
          <span>보이스 합성</span>
          <span>우회 시도</span>
        </div>

        {/* 설명 */}
        <div className="desc-box">
          {result?.description}
        </div>

        {/* detection */}
        <div className="section-title">DETECTION DETAILS</div>

        {detections.map((item, i) => (
          <div key={i} className="detect-card">
            <div>
              <div className="detect-title">{item.title}</div>
              <div className="detect-desc">{item.description}</div>
            </div>

            <span className="badge">{item.status}</span>
          </div>
        ))}

        {/* 신고 */}
        <div className="report-card">

        <h3>

        긴급 신고

        </h3>

        <div className="report-buttons">

        <button>

        🚓

        112

        </button>

        <button>

        ☎

        1332

        </button>

        <button>

        🛡

        118

        </button>

        <button>

        💻

        eCRM

        </button>

        </div>

        </div>

        <div className="sheet-buttons">

        <button
        className="copy-btn"
        >

        결과 복사

        </button>

        <button
        className="close-btn"
        onClick={onClose}
        >

        닫기

        </button>

        </div>

      </div>
    </div>
  );
}
# TrustChain

AI 기반 실시간 사기·딥페이크 탐지 플랫폼

> 송금 전, 최전방에서 사기를 차단합니다.

🔗 **Demo**: https://nous-trustchain.vercel.app/
📦 **Repo**: https://github.com/TW1OO/scamshield

---

## 소개

TrustChain은 보이스피싱, 딥페이크 통화, 리딩방·메신저 사기 등 다양한 형태의 사기를 실시간으로 탐지하는 AI 기반 서비스입니다. 대부분의 사기 탐지 서비스가 피해 발생 후 신고·조회 단계에 머무는 것과 달리, TrustChain은 대화와 통화가 오가는 **최초 접점 단계**에서 위험 신호를 잡아내는 것을 목표로 합니다.

## 핵심 기능

### 1. 대화 분석 (Conversation Guard)
텍스트 대화 내역 또는 메신저 스크린샷을 업로드하면 AI가 대화를 읽고, 사기 특유의 패턴(기관 사칭, 급박감 조성, 계좌·금전 요구, 비밀 유지 요청 등)을 종합적으로 분석해 위험도(낮음~매우 높음)와 판단 근거, 대응 지침을 제시합니다.
- 스크린샷 업로드 시 이미지에서 대화 내용을 자동으로 추출(OCR)한 뒤 분석까지 이어서 수행합니다.
- 단순 키워드 매칭이 아니라, 지인 간 일상 대화(더치페이, 회비 정산 등)와 실제 사기 패턴을 구분하도록 프롬프트가 튜닝되어 있습니다.

### 2. 미디어 분석 (Media Guard)
- **통화 녹화 → 대화 분석**: 실시간 통화 화면·음성을 녹화하면 음성을 텍스트로 변환(STT)한 뒤 대화 분석 엔진으로 위험도를 판별합니다.
- **딥페이크 영상 탐지**: 업로드된 영상에서 일정 간격으로 프레임을 추출해 Hugging Face의 딥페이크 판별 모델(`Deep-Fake-Detector-v2-Model`)로 프레임별 점수를 매기고, 평균 점수로 최종 위험도를 산출합니다.
- **AI 음성(딥보이스) 탐지**: 업로드된 음성 파일을 Reality Defender API로 분석해 AI 생성 음성 여부와 신뢰도를 판별합니다.

## 기술 스택

| 영역 | 스택 |
|---|---|
| Frontend | React 19, Vite 8, lucide-react |
| Backend | FastAPI, SQLAlchemy (SQLite), Uvicorn |
| 대화/이미지 분석 | Llama 3.3 70B / Llama 3.2 90B Vision (NVIDIA API) |
| 딥페이크 영상 탐지 | Hugging Face Inference API (`prithivMLmods/Deep-Fake-Detector-v2-Model`), OpenCV 프레임 추출 |
| 딥보이스(AI 음성) 탐지 | Reality Defender API |
| 프론트엔드 보조 분석 | Gemini 2.5 Flash |
| Lint | oxlint |
| Deployment | Vercel |

## 로컬 실행 방법

### Backend (FastAPI)

```bash
git clone https://github.com/TW1OO/scam_shield.git
cd scam_shield/backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# .env 파일 생성 후 아래 환경변수 설정
# NVIDIA_API_KEY=your_api_key_here
# REALITY_DEFENDER_API_KEY=your_api_key_here
# HUGGINGFACE_API_KEY=your_api_key_here

# 서버 실행
uvicorn main:app --reload
```

### Frontend (React + Vite)

```bash
cd scam_shield/frontend

# 패키지 설치
npm install

# .env 파일 생성 후 아래 환경변수 설정
# VITE_API_BASE_URL=http://localhost:8000
# VITE_GEMINI_API_KEY=...

# 개발 서버 실행
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

## 폴더 구조

```
scam_shield/
├── api/                     # Vercel 서버리스 엔트리포인트
├── backend/                 # FastAPI 서버
│   ├── main.py               # 앱 엔트리포인트
│   ├── database.py           # SQLite 연결 설정
│   ├── models.py              # Recording 모델
│   ├── routers/
│   │   ├── chat.py             # 대화 분석 API (/chat/analyze, /chat/analyze-image)
│   │   ├── call.py             # 통화 녹화 API (/call/record, /call/recordings)
│   │   ├── video.py            # 딥페이크 영상 분석 API (/video/analyze)
│   │   └── deepvoice.py        # 딥보이스 탐지 API (/deepvoice/analyze)
│   └── services/
│       ├── chat_service.py     # 대화/이미지 분석 로직 (NVIDIA API)
│       ├── call_service.py     # 화면·음성 녹화 로직
│       ├── video_service.py    # 프레임 추출 + 딥페이크 탐지 (Hugging Face)
│       └── deepvoice_service.py  # AI 음성 탐지 (Reality Defender)
├── frontend/                 # React + Vite 프론트엔드
│   ├── src/
│   │   ├── components/        # Dashboard, ConversationGuard, MediaGuard 등
│   │   ├── hooks/              # useGeminiAnalysis, useSpeechRecognition 등
│   │   └── utils/               # gemini.js, fileToBase64 등
│   └── vite.config.js
├── requirements.txt
├── vercel.json
└── README.md
```

## 로드맵

- [x] 대화 분석 API (텍스트 / 이미지 업로드)
- [x] 통화 화면·음성 실시간 녹화 및 위험도 분석
- [x] 딥페이크 영상 탐지 연동 (Hugging Face)
- [x] AI 음성(딥보이스) 탐지 연동 (Reality Defender)
- [x] 프론트엔드 UI/UX 설계 및 배포
- [ ] 신종 사기 패턴 B2B/B2G 데이터 피딩 구조 설계
- [ ] 프론트엔드 ↔ 백엔드 API 프로덕션 완전 연동

## 라이선스

이 프로젝트는 코드게이트 AI 스타트업 해커톤 예선 출품작입니다.

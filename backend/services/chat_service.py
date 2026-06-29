from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
)

SYSTEM_PROMPT = """당신은 보이스피싱 탐지 전문 AI입니다.
사용자가 채팅 내역을 제공하면, 대화 전체의 문맥을 분석하여 보이스피싱 가능성을 판단하세요.

다음 패턴들을 중점적으로 분석하세요:
- 기관 사칭: 검찰, 경찰, 금융감독원, 국세청, 은행 직원 등을 사칭
- 급박감 조성: "지금 당장", "오늘 안에", "빨리 하지 않으면 큰일" 등의 압박
- 금전/계좌 요구: 송금, 계좌번호 요청, 현금 인출 요구
- 개인정보 요구: 주민등록번호, 계좌 비밀번호, 카드번호 등
- 비밀 유지 요청: 가족이나 주변인에게 말하지 말라는 요구
- 대출 빙자: 저금리 대출, 정부 지원금 등을 미끼로 사용
- 가족 사칭: 납치, 사고를 빙자한 가족 사칭

반드시 아래 JSON 형식으로만 답변하세요. JSON 외 다른 텍스트는 절대 포함하지 마세요:
{
  "risk_level": "낮음 | 보통 | 높음 | 매우 높음",
  "probability": 0~100 사이의 정수,
  "detected_patterns": ["탐지된 패턴 목록"],
  "reasons": ["판단 근거 목록"],
  "recommendation": "사용자에게 전달할 행동 지침"
}"""


def analyze_chat(messages: list[dict]) -> dict:
    conversation = "\n".join(
        f"[{msg['sender']}]: {msg['content']}" for msg in messages
    )

    response = client.chat.completions.create(
        model="meta/llama-3.3-70b-instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"다음 채팅 내역을 분석해주세요:\n\n{conversation}"},
        ],
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()

    # JSON 블록만 추출
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)

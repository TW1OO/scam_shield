export async function copyProofData(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }

    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";

    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();

    const success = document.execCommand("copy");
    document.body.removeChild(textarea);

    return success;
  } catch (err) {
    console.error(err);
    return false;
  }
}

export function buildProofReport({
  risk,
  description,
  content,
}) {
  return `
[TrustChain AI 피싱 사기 정밀 검증 보고서]

위험도 : ${risk}
분석 결과 : ${description}

분석 대상
${content}

※ 경찰청 및 금융감독원 제출용 참고자료
`.trim();
}

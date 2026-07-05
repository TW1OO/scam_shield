export const MODEL_NAME = "gemini-2.5-flash-preview-09-2025";

export async function callGeminiAPI(apiKey, payload) {
  const url =
    `https://generativelanguage.googleapis.com/v1beta/models/${MODEL_NAME}:generateContent?key=${apiKey}`;

  const maxAttempts = 5;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        return await response.json();
      }

      console.warn(`Attempt ${attempt + 1} failed`, await response.text());
    } catch (err) {
      console.error(err);
    }

    if (attempt < maxAttempts - 1) {
      const delay = Math.pow(2, attempt + 1) * 1000;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw new Error("Gemini API 호출 실패");
}

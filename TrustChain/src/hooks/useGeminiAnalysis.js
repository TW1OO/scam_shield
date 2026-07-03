import { useState } from "react";

export default function useGeminiAnalysis(apiKey) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function analyze(payload) {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      if (!res.ok) {
        throw new Error(await res.text());
      }

      const data = await res.json();

      const text =
        data.candidates?.[0]?.content?.parts?.[0]?.text ?? "";

      const clean = text
        .replace(/```json/g, "")
        .replace(/```/g, "")
        .trim();

      const parsed = JSON.parse(clean);

      setResult(parsed);

      return parsed;
    } catch (e) {
      setError(e);
      throw e;
    } finally {
      setLoading(false);
    }
  }

  return {
    analyze,
    loading,
    result,
    error,
  };
}
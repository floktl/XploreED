const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export async function streamAiAnswer(
  question: string,
  onChunk: (chunk: string) => void
): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/ask-ai-stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ question }),
  });

  if (!res.ok || !res.body) {
    throw new Error("Failed to stream AI answer");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split(/\n\n/);
    buffer = parts.pop() || "";
    for (const part of parts) {
      const line = part.trim();
      if (line.startsWith("data:")) {
        const data = line.replace(/^data:\s*/, "");
        if (data === "[DONE]") {
          return;
        }
        onChunk(data);
      }
    }
  }
}

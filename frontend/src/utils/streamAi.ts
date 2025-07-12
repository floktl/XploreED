const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export async function streamAiAnswer(
    question: string,
    onChunk: (chunk: { type: string; text: string }) => void,
    pageContext?: any
): Promise<void> {
    const res = await fetch(`${BASE_URL}/api/ask-ai-stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ question, pageContext }),
    });

    // If not a stream, just parse JSON and call onChunk once
    if (!res.body || !res.headers.get("content-type")?.includes("stream")) {
        const data = await res.json();
        if (data.answer) {
            onChunk({ type: "paragraph", text: data.answer });
        } else {
            onChunk({ type: "paragraph", text: "[No answer returned by AI]" });
        }
        return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let lastText = "";

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
                if (data === "[DONE]") return;
                try {
                    const parsed = JSON.parse(data);
                    // Only update if the text has changed
                    if (parsed.text !== lastText) {
                        onChunk(parsed);
                        lastText = parsed.text;
                    }
                } catch (e) {
                    console.warn("Failed to parse stream chunk:", data);
                }
            }
        }
    }
}

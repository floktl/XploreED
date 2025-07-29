"""Helper functions for misc AI routes."""

import json
from flask import Response, current_app # type: ignore
from external.mistral.client import send_prompt


def stream_ai_answer(context: str) -> Response:
    """Stream a long answer from Mistral as Server-Sent Events, using context-aware prompt."""
    def generate():
        try:
            # print(f"\033[92m[MISTRAL CALL] stream_ai_answer\033[0m", flush=True)
            with send_prompt(
                "You are an assistant for the XplorED app. Use the app and user info to answer questions about the platform, features, or user progress. Always be helpful and specific.",
                {"role": "user", "content": context},
                temperature=0.3,
                stream=True,
            ) as resp:
                buffer = ""
                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        if line.strip() == "data: [DONE]":
                            break
                        if line.startswith("data:"):
                            line = line[len("data:"):].strip()
                        data = json.loads(line)
                        chunk = (
                            data.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content")
                        )
                        if chunk:
                            # Stream word by word
                            words = chunk.split()
                            for word in words:
                                buffer += (" " if buffer else "") + word
                                structured = {"type": "paragraph", "text": buffer.strip()}
                                yield f"data: {json.dumps(structured, ensure_ascii=False)}\n\n"
                    except Exception:
                        continue
                if buffer.strip():
                    yield f"data: {json.dumps({'type': 'paragraph', 'text': buffer.strip()}, ensure_ascii=False)}\n\n"
        except Exception as e:
            current_app.logger.error("Streaming error: %s", e)
        yield "data: [DONE]\n\n"

    return Response(generate(), mimetype="text/event-stream")


"""Helper functions for misc AI routes."""

import json
from flask import Response, current_app
from .helpers import send_prompt


def stream_ai_answer(question: str) -> Response:
    """Stream a long answer from Mistral as Server-Sent Events."""

    def generate():
        try:
            with send_prompt(
                "You are a helpful German teacher.",
                {"role": "user", "content": question},
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
                            buffer += chunk
                            buffer = buffer.replace("**", "")
                            if buffer.endswith((".", "!", "?")):
                                structured = {"type": "paragraph", "text": buffer.strip()}
                                yield f"data: {json.dumps(structured, ensure_ascii=False)}\n\n"
                                buffer = ""
                    except Exception:
                        continue
                if buffer.strip():
                    yield f"data: {json.dumps({'type': 'paragraph', 'text': buffer.strip()}, ensure_ascii=False)}\n\n"
        except Exception as e:
            current_app.logger.error("Streaming error: %s", e)
        yield "data: [DONE]\n\n"

    return Response(generate(), mimetype="text/event-stream")


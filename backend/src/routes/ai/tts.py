
"""Text to speech endpoint."""

import os
from flask import request, jsonify, Response
from elevenlabs.client import ElevenLabs

from . import ai_bp


@ai_bp.route("/tts", methods=["POST"])
def tts():
    """Convert text to speech using the ElevenLabs API."""
    data = request.get_json()
    text = data.get("text", "")
    voice_id = data.get("voice_id", "JBFqnCBsd6RMkjVDRZzb")
    model_id = data.get("model_id", "eleven_multilingual_v2")

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return jsonify({"error": "API key not set"}), 500

    client = ElevenLabs(api_key=api_key)
    try:
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            output_format="mp3_44100_128",
        )
        return Response(audio, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500




// Text-to-Speech service utility

export const playTextToSpeech = async (text, voiceId, modelId) => {
    if (!text?.trim()) return;

    const response = await fetch("http://localhost:5050/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            text: text,
            voice_id: voiceId,
            model_id: modelId,
        }),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error("Failed to fetch audio: " + errorText);
    }

    const audioData = await response.arrayBuffer();
    const blob = new Blob([audioData], { type: "audio/mpeg" });
    const urlObject = URL.createObjectURL(blob);

    const audio = new Audio(urlObject);
    await audio.play();

    return audio;
};

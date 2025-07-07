export default function diffWords(userAnswer, correctAnswer) {
    if (!userAnswer && !correctAnswer) return null;
    const userTokens = String(userAnswer || "").split(/\s+/);
    const correctTokens = String(correctAnswer || "").split(/\s+/);
    const len = Math.max(userTokens.length, correctTokens.length);
    const parts = [];
    for (let i = 0; i < len; i++) {
        const u = userTokens[i];
        const c = correctTokens[i];
        if (u && c && u.replace(/[.,!?]/g, '').toLowerCase() === c.replace(/[.,!?]/g, '').toLowerCase()) {
            parts.push(
                <span key={"c" + i} className="text-green-600">
                    {c}
                </span>
            );
        } else {
            if (u) {
                parts.push(
                    <span key={"u" + i} className="text-red-600">
                        {u}
                    </span>
                );
            }
            if (c) {
                parts.push(
                    <span key={"r" + i} className="text-green-600">
                        {c}
                    </span>
                );
            }
        }
        parts.push(' ');
    }
    return <>{parts}</>;
}

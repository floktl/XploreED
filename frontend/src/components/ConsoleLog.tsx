import React from "react";

export interface LogEntry {
    text: string;
    count: number;
}

export default function ConsoleLog({ logs }: { logs: LogEntry[] }) {
    if (!logs.length) return null;
    return (
        <div className="chat-console mt-2">
            {logs.map((log, idx) => (
                <div key={idx} className="whitespace-pre-wrap">
                    {log.text}{log.count > 1 ? ` (x${log.count})` : ""}
                </div>
            ))}
        </div>
    );
}

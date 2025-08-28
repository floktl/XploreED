import Card from "../../../common/UI/Card";
import { CheckCircle, XCircle } from "lucide-react";

export default function ProfileStatsTable({ results }) {
  if (!results || results.length === 0) return null;

  return (
    <Card fit className="overflow-x-auto">
      <table className="min-w-full">
        <thead>
          <tr>
            <th className="px-4 py-2 text-left">Level</th>
            <th className="px-4 py-2 text-left">Correct</th>
            <th className="px-4 py-2 text-left">Answer</th>
            <th className="px-4 py-2 text-left">Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r, i) => (
            <tr key={i}>
              <td className="px-4 py-2">{r.level}</td>
              <td className="px-4 py-2">
                {r.correct ? (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-600" />
                )}
              </td>
              <td className="px-4 py-2">{r.answer}</td>
              <td className="px-4 py-2">{new Date(r.timestamp).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

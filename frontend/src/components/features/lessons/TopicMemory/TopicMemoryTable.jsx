import Card from "../../../common/UI/Card";

export default function TopicMemoryTable({ filteredTopics, darkMode }) {
  return (
    <Card fit className="overflow-x-auto hidden sm:block">
      <table className={`min-w-full border rounded-lg overflow-hidden ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
        <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"} style={{position: 'sticky', top: 0, zIndex: 2}}>
          <tr>
            <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Grammar</th>
            <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Topic</th>
            <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Skill</th>
            <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Context</th>
            <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Ease</th>
            <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Interval</th>
            <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Next</th>
            <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Reps</th>
          </tr>
        </thead>
        <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
          {filteredTopics.map((t) => (
            <tr key={t.id} className={darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"}>
              <td className="px-4 py-2 font-medium">{t.grammar || "-"}</td>
              <td className="px-4 py-2">{t.topic || "-"}</td>
              <td className={`px-4 py-2 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>{t.skill_type}</td>
              <td className="px-4 py-2 whitespace-nowrap max-w-xs overflow-hidden text-ellipsis">{t.context}</td>
              <td className="px-4 py-2">{Number(t.ease_factor).toFixed(2)}</td>
              <td className="px-4 py-2">{t.intervall}</td>
              <td className="px-4 py-2">{t.next_repeat ? new Date(t.next_repeat).toLocaleDateString() : ""}</td>
              <td className="px-4 py-2">{t.repetitions}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

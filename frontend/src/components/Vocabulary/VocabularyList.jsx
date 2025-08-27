import React from "react";
import Card from "../UI/Card";
import useMediaQuery from "../../utils/useMediaQuery";

export default function VocabularyList({
  vocab,
  typeFilter,
  onVocabSelect,
  darkMode
}) {
  const isMobile = useMediaQuery("(max-width: 640px)");

  const getFilteredVocab = () => {
    if (!vocab || !Array.isArray(vocab)) return [];
    if (!typeFilter) return vocab;
    return vocab.filter(v => v.word_type === typeFilter);
  };

  const filteredVocab = getFilteredVocab();

  if (filteredVocab.length === 0) {
    return (
      <Card className="text-center py-8">
        <div className="text-gray-500">
          {typeFilter ? `No ${typeFilter} vocabulary found.` : "No vocabulary found."}
        </div>
      </Card>
    );
  }

  return (
    <Card>
      {isMobile ? (
        <div className="grid gap-3">
          {filteredVocab.map((v, i) => (
            <div
              key={i}
              className={`rounded-lg border ${darkMode ? "border-gray-700 bg-gray-900" : "border-gray-200 bg-white"} p-3 shadow-sm flex flex-col gap-1 relative cursor-pointer transition hover:shadow-md`}
              onClick={() => onVocabSelect(v)}
            >
              <div className="flex items-center justify-between">
                <div className="font-bold text-lg">{v.vocab}</div>
              </div>
              {v.article && <div className="text-xs text-blue-700 font-semibold">{v.article}</div>}
              <div className="text-sm"><span className="font-semibold">Translation:</span> {v.translation}</div>
              <div className="text-sm"><span className="font-semibold">Type:</span> {v.word_type}</div>
              {v.next_review && <div className="text-xs text-gray-500">Due: {new Date(v.next_review).toLocaleDateString()}</div>}
            </div>
          ))}
        </div>
      ) : (
        <div className="w-full rounded-lg overflow-x-auto">
          <table className={`min-w-full border-separate border-spacing-0 ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
            <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
              <tr>
                <th className="sticky left-0 z-10 bg-inherit px-4 py-2 text-left">German Word</th>
                <th className="px-4 py-2 text-left">Article</th>
                <th className="px-4 py-2 text-left">English Translation</th>
                <th className="px-4 py-2 text-left">Type</th>
                <th className="px-4 py-2 text-left">Due</th>
                <th className="px-2 py-2"></th>
              </tr>
            </thead>
            <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
              {filteredVocab.map((v, i) => (
                <tr key={i} className={darkMode ? "hover:bg-gray-700 cursor-pointer" : "hover:bg-gray-50 cursor-pointer"} onClick={() => onVocabSelect(v)}>
                  <td className="sticky left-0 z-10 bg-inherit px-4 py-2 font-medium">{v.vocab}</td>
                  <td className="px-4 py-2">{v.article || ""}</td>
                  <td className={`px-4 py-2 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>{v.translation}</td>
                  <td className="px-4 py-2 capitalize">{v.word_type || ""}</td>
                  <td className="px-4 py-2">{v.next_review ? new Date(v.next_review).toLocaleDateString() : ""}</td>
                  <td className="px-2 py-2">
                    {/* Removed delete button from table row */}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

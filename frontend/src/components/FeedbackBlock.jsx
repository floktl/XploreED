import React, { useState } from "react";
import { CheckCircle, XCircle } from "lucide-react";
import diffWords from "../utils/diffWords";
import Spinner from "./UI/Spinner";
import { lookupVocabWord } from "../api";
import VocabDetailModal from "./VocabDetailModal";

function onlyWrongWords(userAnswer, correctAnswer) {
  if (!userAnswer && !correctAnswer) return null;
  const userTokens = String(userAnswer || "").split(/\s+/);
  const correctTokens = String(correctAnswer || "").split(/\s+/);
  const len = Math.max(userTokens.length, correctTokens.length);
  const parts = [];
  for (let i = 0; i < len; i++) {
    const u = userTokens[i];
    const c = correctTokens[i];
    if (!u) continue;
    if (!c || u.replace(/[.,!?]/g, '').toLowerCase() !== c.replace(/[.,!?]/g, '').toLowerCase()) {
      parts.push(
        <span key={"u" + i} className="text-red-600 underline decoration-dotted cursor-help" title={c ? `Expected: '${c}'` : "Unexpected word"}>{u}</span>
      );
      parts.push(' ');
    }
  }
  return <>{parts}</>;
}

function onlyMissingWords(userAnswer, correctAnswer) {
  if (!userAnswer && !correctAnswer) return null;
  const userTokens = String(userAnswer || "").split(/\s+/);
  const correctTokens = String(correctAnswer || "").split(/\s+/);
  const len = Math.max(userTokens.length, correctTokens.length);
  const parts = [];
  for (let i = 0; i < len; i++) {
    const u = userTokens[i];
    const c = correctTokens[i];
    if (!c) continue;
    if (!u || u.replace(/[.,!?]/g, '').toLowerCase() !== c.replace(/[.,!?]/g, '').toLowerCase()) {
      parts.push(
        <span key={"c" + i} className="text-green-600">{c}</span>
      );
      parts.push(' ');
    }
  }
  return <>{parts}</>;
}

function diffWithNeutral(userAnswer, correctAnswer) {
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
        <span key={"n" + i} className="text-white dark:text-gray-100">{u}</span>
      );
    } else if (u) {
      parts.push(
        <span key={"u" + i} className="text-red-600 underline decoration-dotted cursor-help" title={c ? `Expected: '${c}'` : "Unexpected word"}>{u}</span>
      );
    }
    parts.push(' ');
  }
  return <>{parts}</>;
}

function diffWithNeutralCorrect(userAnswer, correctAnswer) {
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
        <span key={"n" + i} className="text-white dark:text-gray-100">{c}</span>
      );
    } else if (c) {
      parts.push(
        <span key={"c" + i} className="text-green-600">{c}</span>
      );
    }
    parts.push(' ');
  }
  return <>{parts}</>;
}

export default function FeedbackBlock({
  status,
  correct,
  alternatives = [],
  explanation,
  userAnswer,
  diff,
  children,
  loading,
  exerciseLoading = false,  // New prop for exercise-level loading
}) {
  const [vocabModal, setVocabModal] = useState(null);
  const [vocabLoading, setVocabLoading] = useState(false);

  const handleWordClick = async (word) => {
    setVocabLoading(true);
    const vocab = await lookupVocabWord(word);
    setVocabLoading(false);
    if (vocab) setVocabModal(vocab);
  };

  return (
    <div className="p-4 rounded bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-100 space-y-2">
      <div className="flex items-center gap-2 font-bold">
        {status === "correct" ? (
          <span className="text-green-700 dark:text-green-400 flex items-center gap-1">
            <CheckCircle className="w-5 h-5" /> Correct!
          </span>
        ) : (
          <span className="text-red-700 dark:text-red-400 flex items-center gap-1">
            <XCircle className="w-5 h-5" /> Incorrect.
          </span>
        )}
      </div>
      {(loading || exerciseLoading) && (
        <div className="flex justify-center items-center py-2">
          <Spinner />
          <span className="ml-2 text-gray-600 dark:text-gray-400 text-sm">Generating detailed feedback...</span>
        </div>
      )}
      {/* Only show the difference (diff) for incorrect answers, if present */}
      {status !== 'correct' && typeof userAnswer !== 'undefined' && typeof correct !== 'undefined' && (
        <div className="mt-2">
          <strong className="text-gray-700 dark:text-gray-200">Difference:</strong>
          <div className="flex flex-col gap-1 ml-2">
            <div>
              <span className="text-gray-500 text-xs">Your answer:</span>
              <div className="font-mono bg-gray-100 dark:bg-gray-800 rounded px-2 py-1 mt-1">
                {diffWithNeutral(userAnswer, correct)}
              </div>
            </div>
            <div>
              <span className="text-gray-500 text-xs">Correct answer:</span>
              <div className="font-mono bg-green-50 dark:bg-green-900 rounded px-2 py-1 mt-1">
                {diffWithNeutralCorrect(userAnswer, correct)}
              </div>
            </div>
          </div>
        </div>
      )}
      <div>
        <strong className="text-blue-700 dark:text-blue-400">Alternative correct answers:</strong>
        {loading ? (
          <div className="flex items-center gap-2 ml-2 mt-1">
            <Spinner size="sm" />
            <span className="text-gray-600 dark:text-gray-400 text-sm">Generating alternatives...</span>
          </div>
        ) : alternatives.length > 0 ? (
          <ul className="list-disc ml-6 mt-1">
            {alternatives.map((alt, i) => (
              <li key={i} className="font-mono">{alt}</li>
            ))}
          </ul>
        ) : (
          <span className="ml-2 text-gray-800 dark:text-gray-100">No alternative correct answers.</span>
        )}
      </div>
      <div>
        <strong className="text-gray-700 dark:text-gray-200">Explanation:</strong>{" "}
        {explanation}
      </div>
      {vocabLoading && <Spinner />}
      {vocabModal && (
        <VocabDetailModal vocab={vocabModal} onClose={() => setVocabModal(null)} />
      )}
      {children}
    </div>
  );
}

import { useState } from "react";
import { CheckCircle, XCircle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import Spinner from "../UI/Spinner";
import { lookupVocabWord, searchVocabWithAI } from "../../../services/api";
import VocabDetailModal from "../../features/vocabulary/VocabDetailModal/VocabDetailModal";

// Import modular components
import FeedbackDifference from "./Components/FeedbackDifference";
import FeedbackAlternatives from "./Components/FeedbackAlternatives";

export default function FeedbackBlock({
  status,
  correct,
  alternatives = [],
  explanation,
  userAnswer,
  diff,
  children,
  loading,
  exerciseLoading = false,
}) {
  const [vocabModal, setVocabModal] = useState(null);
  const [vocabLoading, setVocabLoading] = useState(false);

  // Trust backend as source of truth; do not render client fallback
  const finalExplanation = explanation;

  const handleWordClick = async (word) => {
    setVocabLoading(true);
    try {
      // First try to lookup the word in existing vocabulary
      let vocab = await lookupVocabWord(word);

      if (vocab) {
        setVocabModal(vocab);
      } else {
        // If not found, search with AI and save it
        vocab = await searchVocabWithAI(word);
        if (vocab) {
          setVocabModal(vocab);
        }
      }
    } catch (error) {
      console.error("Error looking up vocabulary:", error);
    } finally {
      setVocabLoading(false);
    }
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

      <FeedbackDifference
        userAnswer={userAnswer}
        correct={correct}
        status={status}
      />

      <FeedbackAlternatives
        alternatives={alternatives}
        loading={loading}
      />

      {finalExplanation && (
        <div>
          <strong className="text-gray-700 dark:text-gray-200">Explanation:</strong>
          <div className="mt-2 prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              components={{
                strong: ({ children }) => (
                  <strong className="font-semibold text-blue-600 dark:text-blue-400">
                    {children}
                  </strong>
                ),
                em: ({ children }) => (
                  <em className="italic text-gray-700 dark:text-gray-300">
                    {children}
                  </em>
                ),
                p: ({ children }) => (
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {children}
                  </p>
                ),
              }}
            >
              {finalExplanation}
            </ReactMarkdown>
          </div>
        </div>
      )}

      {vocabLoading && <Spinner />}
      {vocabModal && (
        <VocabDetailModal vocab={vocabModal} onClose={() => setVocabModal(null)} />
      )}
      {children}
    </div>
  );
}

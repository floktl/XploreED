import React from "react";
import { Rocket } from "lucide-react";
import { Input } from "../UI/UI";
import Button from "../UI/Button";
import Alert from "../UI/Alert";
import Spinner from "../UI/Spinner";

export default function TranslationForm({
  english,
  setEnglish,
  studentInput,
  setStudentInput,
  error,
  loading,
  onTranslate,
  darkMode
}) {
  return (
    <form
      className="space-y-6 max-w-2xl mx-auto"
      onSubmit={(e) => {
        e.preventDefault();
        onTranslate();
      }}
    >
      <div className="space-y-2">
        <label className={`block text-sm font-medium ${darkMode ? "text-gray-200" : "text-gray-700"}`}>
          English Text to Translate
        </label>
        <Input
          autoFocus
          placeholder="Enter English word, phrase, or sentence..."
          value={english}
          onChange={(e) => setEnglish(e.target.value)}
          className="w-full"
        />
      </div>

      <div className="space-y-2">
        <label className={`block text-sm font-medium ${darkMode ? "text-gray-200" : "text-gray-700"}`}>
          Your German Translation
        </label>
        <Input
          placeholder="Type your German translation here..."
          value={studentInput}
          onChange={(e) => setStudentInput(e.target.value)}
          className="w-full"
        />
      </div>

      {error && <Alert type="warning">{error}</Alert>}
      {loading && <Spinner />}

      <div className="flex flex-col sm:flex-row gap-3">
        <Button variant="primary" className="w-full gap-2" onClick={onTranslate} disabled={loading}>
          <Rocket className="w-4 h-4" />
          {loading ? "Translating..." : "Get Feedback"}
        </Button>
      </div>
    </form>
  );
}

import clsx from "clsx";

export default function LanguageSection({ language, setLanguage, darkMode }) {
  return (
    <div className="space-y-2">
      <label className="block font-semibold">Language</label>
      <select
        className={clsx(
          "border rounded px-3 py-2",
          darkMode
            ? "bg-gray-800 text-white border-gray-700"
            : "bg-white text-gray-900 border-gray-200"
        )}
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
      >
        <option value="en">English</option>
        <option value="de">Deutsch</option>
      </select>
    </div>
  );
}

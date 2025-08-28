
export default function TranslatorHeader({ darkMode }) {
  return (
    <div className="text-center mb-8">
      <h1 className={`text-3xl font-bold mb-2 ${darkMode ? "text-blue-400" : "text-blue-600"}`}>
        Translation Practice
      </h1>
      <p className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
        Practice translating English to German and get instant feedback
      </p>
    </div>
  );
}

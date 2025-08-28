
export default function LevelGameInstructions({ darkMode }) {
  return (
    <p className={`mb-4 text-center text-lg ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
      Drag and drop words to reorder the sentence
    </p>
  );
}

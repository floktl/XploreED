
export default function LessonsHeader({ darkMode }) {
  return (
    <p className={`text-center ${darkMode ? "text-gray-300" : "text-gray-600"}`}>
      Overview of your past and upcoming lessons
    </p>
  );
}

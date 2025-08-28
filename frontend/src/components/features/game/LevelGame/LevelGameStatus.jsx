
export default function LevelGameStatus({ status }) {
  if (!status) return null;

  return (
    <div className={`text-sm mb-4 text-center ${
      status.includes("Error") ? "text-red-500" : "text-blue-500"
    }`}>
      {status}
    </div>
  );
}

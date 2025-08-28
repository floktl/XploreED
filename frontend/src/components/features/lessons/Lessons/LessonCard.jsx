import { useNavigate } from "react-router-dom";
import Card from "../../../common/UI/Card";
import Button from "../../../common/UI/Button";

export default function LessonCard({ lesson }) {
	const navigate = useNavigate();

	return (
		<Card>
			<div className="flex justify-between items-center">
				<div className="flex justify-start items-baseline w-1/2 min-w-0 overflow-hidden">
					<h3 className="font-semibold truncate" title={lesson.title}>
						{lesson.title || `Lesson ${lesson.lesson_id}`}
					</h3>
					<p className={`text-sm mx-2 flex items-center space-x-1 ${lesson.completed ? "text-green-600" : "text-gray-500"}`}>
						{lesson.completed ? (
							<>
								<span className="text-base">✅</span>
								<span>Completed</span>
							</>
						) : (
							<>
								<span className="text-base">📊</span>
								<span>{Math.round(lesson.percent_complete || 0)}% Complete</span>
							</>
						)}
					</p>
					{lesson.last_attempt && (
						<p className="text-xs text-gray-400">
							Last Attempt: {new Date(lesson.last_attempt).toLocaleString()}
						</p>
					)}
				</div>
				<Button
					variant="secondary"
					type="button"
					className="relative overflow-hidden w-1/2"
					onClick={() => navigate(`/lesson/${lesson.lesson_id}`)}
				>
					<span className="relative z-10">
						{lesson.completed ? "🔁 Review" : "▶️ Continue"}
					</span>
					{!lesson.completed && (
						<span
							className="absolute top-0 left-0 h-full bg-blue-500 opacity-30"
							style={{ width: `${lesson.percent_complete || 0}%` }}
						/>
					)}
				</Button>
			</div>
		</Card>
	);
}

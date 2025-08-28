import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Container, Title, Input } from "../../components/common/UI/UI";
import Card from "../../components/common/UI/Card";
import Button from "../../components/common/UI/Button";
import Alert from "../../components/common/UI/Alert";
import ErrorPageView from "./ErrorPageView";
import LessonEditor from "../../components/features/lessons/LessonEditor/LessonEditor";
import { Pencil } from "lucide-react";
import { getLessonById, updateLesson } from "../../services/api";

export default function LessonEdit() {
	const { id } = useParams();
	const navigate = useNavigate();
	const [lesson, setLesson] = useState(null);
	const [error, setError] = useState("");
	const [fatalError, setFatalError] = useState(false);

	useEffect(() => {
		const fetchLesson = async () => {
			try {
				const data = await getLessonById(id);
				setLesson(data);
			} catch (err) {
				setError("Could not load lesson.");
				setFatalError(true);
			}
		};
		fetchLesson();
	}, [id]);


	const handleSubmit = async (e) => {
		e.preventDefault();
		try {
			const updated = await updateLesson(id, lesson);
			if (!updated.ok && updated !== true) throw new Error("Failed to update");
			alert("Lesson updated!");
			navigate("/admin-panel");
		} catch (err) {
			setError("Failed to save changes.");
			setFatalError(true);
		}
	};

	if (fatalError) return <ErrorPageView />;
	if (!lesson) return <p className="text-center mt-10">Loading lesson...</p>;

	return (
		<Container>
			<Title className="mb-6">
				<div className="flex items-center gap-2">
					<Pencil className="w-6 h-6" />
					<span>Edit Lesson {id}</span>
				</div>
			</Title>
			{error && <Alert type="danger">{error}</Alert>}

			<Card>
				<form className="flex flex-col gap-4" onSubmit={handleSubmit}>
					<div>
						<label className="block mb-1 font-medium">Title</label>
						<Input
							value={lesson.title}
							onChange={(e) => setLesson({ ...lesson, title: e.target.value })}
							required
						/>
					</div>
					<div>
						<label className="block mb-1 font-medium">Content</label>
						<div>
							<label className="block mb-1 font-medium">Content</label>
							<LessonEditor
								content={lesson.content}
								onContentChange={(html) => setLesson({ ...lesson, content: html })}
								aiEnabled={!!lesson.ai_enabled}
								onToggleAI={() =>
									setLesson({ ...lesson, ai_enabled: lesson.ai_enabled ? 0 : 1 })
								}
							/>
						</div>
					</div>
					<div>
						<label className="block mb-1 font-medium">Target User (optional)</label>
						<Input
							value={lesson.target_user ?? ""}
							onChange={(e) => setLesson({ ...lesson, target_user: e.target.value })}
						/>
					</div>
					<label className="flex items-center gap-2">
						<input
							type="checkbox"
							checked={!!lesson.ai_enabled}
							onChange={(e) =>
								setLesson({ ...lesson, ai_enabled: e.target.checked ? 1 : 0 })
							}
						/>
						<span>Include AI Exercises</span>
					</label>
					<Button type="submit" variant="success">
						💾 Save Changes
					</Button>
				</form>
			</Card>
		</Container>
	);
}


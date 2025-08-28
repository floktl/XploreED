import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "../../components/common/UI/UI";
import Footer from "../../components/common/UI/Footer";
import Button from "../../components/common/UI/Button";
import { ArrowLeft } from "lucide-react";
import { CheckCircle, Brain, Target, Sparkles } from "lucide-react";
import useAppStore from "../../store/useAppStore";
import { getReadingExercise, submitReadingAnswers } from "../../services/api";
import { PageLayout } from "../../components/layout";
import {
	AIReadingHeader,
	AIReadingSetup,
	AIReadingProgress,
	AIReadingContent,
	AIReadingFooter,
	AIReadingError
} from "../../components/features/ai";

function makeSnippet(text, answer, range = 20) {
	const index = text.toLowerCase().indexOf(answer.toLowerCase());
	if (index === -1)
		return "";
	const start = Math.max(0, index - range);
	const end = Math.min(text.length, index + answer.length + range);
	const snippet = text.slice(start, end);
	const escapedAnswer = answer.replace(/([.*+?^${}()|[\]\\])/g, "\\$1");
	const regex = new RegExp(escapedAnswer, "i");
	return snippet.replace(regex, (match) => `<strong class='text-green-600'>${match}</strong>`);
}

function guessCorrectAnswers(text, questions) {
	const lowered = text.toLowerCase();
	const map = {};
	questions.forEach((q) => {
		const found = q.options.find((opt) => lowered.includes(opt.toLowerCase()));
		if (found)
		{
			map[q.id] = found;
		}
	});
	return map;
}

export default function AIReadingView()
{
	const [style, setStyle] = useState("story");
	const [data, setData] = useState(null);
	const [exerciseId, setExerciseId] = useState(null);
	const [answers, setAnswers] = useState({});
	const [submitted, setSubmitted] = useState(false);
	const [loading, setLoading] = useState(false);
	const [results, setResults] = useState({});
	const [feedback, setFeedback] = useState({});
	const [progressPercentage, setProgressPercentage] = useState(0);
	const [progressStatus, setProgressStatus] = useState("Initializing...");
	const [progressIcon, setProgressIcon] = useState(Brain);
	const [feedbackBlocks, setFeedbackBlocks] = useState([]);
	const [apiError, setApiError] = useState(false);
	const navigate = useNavigate();
	const darkMode = useAppStore((s) => s.darkMode);
	const addBackgroundActivity = useAppStore((s) => s.addBackgroundActivity);
	const updateBackgroundActivity = useAppStore((s) => s.updateBackgroundActivity);
	const removeBackgroundActivity = useAppStore((s) => s.removeBackgroundActivity);

	const startExercise = async () => {
		setLoading(true);
		setAnswers({});
		setResults({});
		setFeedback({});
		setSubmitted(false);
		setProgressPercentage(0);
		setProgressStatus("Initializing...");
		setProgressIcon(Brain);
		let progressInterval;
		const progressSteps = [
			{ percentage: 15, status: "Analyzing your reading level...", icon: Target },
			{ percentage: 35, status: "Reviewing your vocabulary...", icon: Sparkles },
			{ percentage: 55, status: "Identifying weak areas...", icon: Brain },
			{ percentage: 75, status: "Generating reading exercise...", icon: Sparkles },
			{ percentage: 90, status: "Finalizing your lesson...", icon: Sparkles },
			{ percentage: 100, status: "Ready!", icon: CheckCircle }
		];
		let currentStep = 0;
		progressInterval = setInterval(() => {
			if (currentStep < progressSteps.length)
			{
				const step = progressSteps[currentStep];
				setProgressPercentage(step.percentage);
				setProgressStatus(step.status);
				setProgressIcon(step.icon);
				currentStep++;
			}
			else
			{
				clearInterval(progressInterval);
			}
		}, 800);
		try
		{
			const d = await getReadingExercise(style);
			setData(d);
			setExerciseId(d.exercise_id || null);
			setProgressPercentage(100);
			setProgressStatus("Ready!");
			setProgressIcon(CheckCircle);
			setApiError(false);
		}
		catch
		{
			setApiError(true);
			setData(null);
			setExerciseId(null);
		}
		finally
		{
			setLoading(false);
			clearInterval(progressInterval);
		}
	};

	const handleSelect = (id, value) => {
		setAnswers((prev) => ({ ...prev, [id]: value }));
	};

	const handleSubmit = async () => {
		if (!data || !exerciseId) return;
		setLoading(true);
		setSubmitted(true);
		const activityId = `reading-save-${Date.now()}`;
		addBackgroundActivity({ id: activityId, label: "Saving vocab and updating memory...", status: "In progress" });
		try
		{
			const result = await submitReadingAnswers(answers, exerciseId);
			let map = {};
			if (result?.results)
			{
				result.results.forEach((r) => {
					if (r.correct_answer)
					{
						map[r.id] = r.correct_answer;
					}
				});
			}
			if (result && result.feedbackBlocks)
			{
				setFeedbackBlocks(result.feedbackBlocks);
			}
			else
			{
				setFeedbackBlocks([]);
			}
			if (Object.keys(map).length === 0)
			{
				map = guessCorrectAnswers(data.text, data.questions);
			}
			setResults(map);
			const fb = {};
			data.questions.forEach((q) => {
				const ans = map[q.id];
				if (ans)
				{
					fb[q.id] = makeSnippet(data.text, ans);
				}
			});
			setFeedback(fb);
			updateBackgroundActivity(activityId, { status: "Done" });
			setTimeout(() => removeBackgroundActivity(activityId), 1200);
		}
		catch (err)
		{
			console.error("Reading submit error:", err);
			updateBackgroundActivity(activityId, { status: "Error" });
			setTimeout(() => removeBackgroundActivity(activityId), 1200);
			setFeedbackBlocks([]);
		}
		finally
		{
			setLoading(false);
		}
	};

	const allQuestionsAnswered = (
		data &&
		typeof data === "object" &&
		Array.isArray(data.questions) &&
		data.questions.length > 0 &&
		data.questions.every((q) => {
			const answer = answers[q.id];
			return answer && answer.trim && answer.trim().length > 0;
		})
	);

	if (apiError)
	{
		return (
			<PageLayout variant="relative">
				<Container className="" bottom={null}>
					<AIReadingHeader />
					<AIReadingError />
				</Container>
				<Footer>
					<Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")} className="gap-2">
						<ArrowLeft className="w-4 h-4" />
						Back
					</Button>
				</Footer>
			</PageLayout>
		);
	}

	if (!data || typeof data !== "object" || !Array.isArray(data.questions)) {
		return (
			<PageLayout variant="relative">
				<Container className="" bottom={null}>
					<AIReadingHeader />
					<AIReadingSetup
						style={style}
						setStyle={setStyle}
						onStartExercise={startExercise}
						loading={loading}
						progressPercentage={progressPercentage}
						progressStatus={progressStatus}
						progressIcon={progressIcon}
					/>
				</Container>
				<Footer>
					<Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")} className="gap-2">
						<ArrowLeft className="w-4 h-4" />
						Back
					</Button>
				</Footer>
			</PageLayout>
		);
	}

	return (
		<PageLayout variant="relative">
			{data && data.questions.length > 0 && !submitted && (
				<AIReadingProgress answers={answers} questionsCount={data.questions.length} />
			)}
			<Container className="" bottom={null}>
				<AIReadingHeader title="Reading Exercise" />
				<AIReadingContent
					data={data}
					answers={answers}
					results={results}
					submitted={submitted}
					feedbackBlocks={feedbackBlocks}
					onSelect={handleSelect}
					loading={loading}
				/>
			</Container>
			<AIReadingFooter
				onNavigate={navigate}
				submitted={submitted}
				onSubmit={handleSubmit}
				allQuestionsAnswered={allQuestionsAnswered}
			/>
		</PageLayout>
	);
}

import React, { useState } from "react";
import Button from "./UI/Button";

export default function AIExerciseBlock({ data })
{
	const [answers, setAnswers] = useState({});
	const [submitted, setSubmitted] = useState(false);
	const [stage, setStage] = useState(0); // 0 = first set, 1 = next set

	if (!data || !Array.isArray(data.exercises))
	{
		return null;
	}

	const currentExercises = stage === 0 ? data.exercises : data.nextExercises || [];
	const feedbackPrompt = stage === 0 ? data.feedbackPrompt : data.nextFeedbackPrompt;

	const handleSelect = (exId, option) =>
	{
		setAnswers((prev) => ({ ...prev, [exId]: option }));
	};

	const handleChange = (exId, value) =>
	{
		setAnswers((prev) => ({ ...prev, [exId]: value }));
	};

	const handleSubmit = () =>
	{
		setSubmitted(true);
	};

	const handleNext = () =>
	{
		setStage(1);
		setSubmitted(false);
		setAnswers({});
	};

	return (
		<div className="space-y-4">
			{stage === 0 && data.instructions && <p>{data.instructions}</p>}
			{stage === 1 && data.nextInstructions && <p>{data.nextInstructions}</p>}

			{currentExercises.length > 0 && (
				<div className="space-y-6">
					{currentExercises.map((ex) => (
						<div key={ex.id} className="mb-4">
							{ex.type === "gap-fill" ? (
								<>
									<div className="mb-2 font-medium">
										{(() =>
										{
											const parts = String(ex.question).split("___");
											return (
												<>
													{parts[0]}
													{answers[ex.id] ? (
														<span className="text-blue-600">{answers[ex.id]}</span>
													) : (
														<span className="text-gray-400">___</span>
													)}
													{parts[1]}
												</>
											);
										})()}
									</div>
									<div className="flex flex-wrap gap-2">
										{ex.options.map((opt) => (
											<Button
												key={opt}
												variant={answers[ex.id] === opt ? "primary" : "secondary"}
												type="button"
												onClick={() => handleSelect(ex.id, opt)}
												disabled={submitted}
											>
												{opt}
											</Button>
										))}
									</div>
								</>
							) : (
								<>
									<label className="block mb-2 font-medium">{ex.question}</label>
									<input
										type="text"
										className="border rounded p-2 w-full"
										value={answers[ex.id] || ""}
										onChange={(e) => handleChange(ex.id, e.target.value)}
										disabled={submitted}
										placeholder="Your answer"
									/>
								</>
							)}

							{submitted && (
								<div className="mt-2">
									{String(answers[ex.id]).trim().toLowerCase() ===
									String(ex.correctAnswer).trim().toLowerCase() ? (
										<span className="text-green-600">✅ Correct!</span>
									) : (
										<span className="text-red-600">
											❌ Incorrect. Correct answer: <b>{ex.correctAnswer}</b>
										</span>
									)}
									<div className="text-xs text-gray-500 mt-1">{ex.explanation}</div>
								</div>
							)}
						</div>
					))}

					{!submitted && (
						<Button type="button" variant="success" onClick={handleSubmit}>
							Submit Answers
						</Button>
					)}

					{submitted && feedbackPrompt && (
						<div className="mt-4 italic text-blue-700 dark:text-blue-300">
							{feedbackPrompt}
						</div>
					)}

					{submitted && stage === 0 && data.nextExercises && data.nextExercises.length > 0 && (
						<Button type="button" variant="primary" onClick={handleNext}>
							Next Exercises
						</Button>
					)}
				</div>
			)}

			{data.vocabHelp && data.vocabHelp.length > 0 && (
				<div className="mt-4">
					<strong>Vocabulary Help:</strong>
					<ul className="list-disc ml-6">
						{data.vocabHelp.map((v, idx) => (
							<li key={v.word || idx}>
								<span className="font-medium">{v.word}</span>: {v.meaning}
							</li>
						))}
					</ul>
				</div>
			)}
		</div>
	);
}

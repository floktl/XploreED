// Feedback parsing utility

export function parseFeedback(feedback) {
  // Simple regex-based section splitting
  const sections = {};
  const translationMatch = feedback.match(/\*\*Translation:\*\*([\s\S]*?)(\*\*|$)/);
  const evaluationMatch = feedback.match(/\*\*Evaluation:\*\*([\s\S]*?)(\*\*|$)/);
  const notesMatch = feedback.match(/\*\*Additional Notes:\*\*([\s\S]*?)(\*\*|$)/);
  const exampleMatch = feedback.match(/Here\'s an example[\s\S]*$/);

  if (translationMatch) sections.translation = translationMatch[1].trim();
  if (evaluationMatch) sections.evaluation = evaluationMatch[1].trim();
  if (notesMatch) sections.notes = notesMatch[1].trim();
  if (exampleMatch) sections.example = exampleMatch[0].trim();

  return sections;
}

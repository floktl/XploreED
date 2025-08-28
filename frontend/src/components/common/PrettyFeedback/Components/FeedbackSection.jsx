import ReactMarkdown from "react-markdown";

export default function FeedbackSection({
  icon: Icon,
  title,
  content,
  colorClass
}) {
  if (!content) return null;

  return (
    <>
      <div className={`flex items-center gap-2 ${colorClass} font-semibold`}>
        <Icon className="w-5 h-5" />
        <span>{title}</span>
      </div>
      <ReactMarkdown className="pl-6">{content}</ReactMarkdown>
    </>
  );
}

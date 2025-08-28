import { ArrowLeft } from "lucide-react";
import Button from "../../../common/UI/Button";
import Footer from "../../../common/UI/Footer";

export default function AIReadingFooter({
  onNavigate,
  submitted,
  onSubmit,
  allQuestionsAnswered
}) {
  return (
    <Footer>
      {!submitted && (
        <Button onClick={onSubmit} variant="success" disabled={!allQuestionsAnswered} className="w-full max-w-xs mx-auto">
          Submit Answers
        </Button>
      )}
      <Button size="md" variant="ghost" type="button" onClick={() => onNavigate("/menu")} className="gap-2">
        <ArrowLeft className="w-4 h-4" />
        Back
      </Button>
    </Footer>
  );
}

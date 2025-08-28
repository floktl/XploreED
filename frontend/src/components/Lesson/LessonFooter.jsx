import Button from "../common/UI/Button";
import Footer from "../common/UI/Footer";
import { ArrowLeft } from "lucide-react";

const LessonFooter = ({ actions, onNavigate }) => {
  return (
    <Footer>
      <div className="flex gap-2">
        {actions}
        <Button
          size="sm"
          variant="ghost"
          type="button"
          onClick={() => onNavigate("/lessons")}
          className="gap-2 rounded-full"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Lessons
        </Button>
      </div>
    </Footer>
  );
};

export default LessonFooter;

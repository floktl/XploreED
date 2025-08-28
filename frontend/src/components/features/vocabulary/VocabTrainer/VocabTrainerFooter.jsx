import { ArrowLeft } from "lucide-react";
import Button from "../../../common/UI/Button";
import Footer from "../../../common/UI/Footer";

export default function VocabTrainerFooter({ onNavigate }) {
  return (
    <Footer>
      <Button variant="link" onClick={() => onNavigate("/vocabulary")} className="gap-1">
        <ArrowLeft className="w-4 h-4" />
        Back to Vocabulary
      </Button>
    </Footer>
  );
}

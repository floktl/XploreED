import { ArrowLeft } from "lucide-react";
import Button from "../../../common/UI/Button";
import Footer from "../../../common/UI/Footer";

export default function AIWeaknessLessonFooter({ onNavigate }) {
  return (
    <Footer>
      <Button size="md" variant="ghost" type="button" onClick={() => onNavigate("/menu")} className="gap-2">
        <ArrowLeft className="w-4 h-4" />
        Back
      </Button>
    </Footer>
  );
}

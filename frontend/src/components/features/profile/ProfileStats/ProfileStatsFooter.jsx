import { ArrowLeft } from "lucide-react";
import Button from "../../../common/UI/Button";
import Footer from "../../../common/UI/Footer";

export default function ProfileStatsFooter({ onNavigate }) {
  return (
    <Footer>
      <Button onClick={() => onNavigate("/admin-panel")} variant="link" className="gap-2">
        <ArrowLeft className="w-4 h-4" />
        Back to Admin Panel
      </Button>
    </Footer>
  );
}

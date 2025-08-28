import { ArrowLeft, Trash2 } from "lucide-react";
import Button from "../../../common/UI/Button";
import Footer from "../../../common/UI/Footer";

export default function TopicMemoryFooter({
  onNavigate,
  onResetFilters,
  onShowClear
}) {
  return (
    <Footer>
      <Button size="md" variant="ghost" type="button" onClick={() => onNavigate("/menu")} className="gap-2">
        <ArrowLeft className="w-4 h-4" />
        Back
      </Button>
      <Button variant="secondary" size="md" onClick={onResetFilters}>
        Reset Filters
      </Button>
      <Button variant="danger" size="md" onClick={onShowClear} className="gap-2">
        <Trash2 className="w-4 h-4" />
        Clear Memory
      </Button>
    </Footer>
  );
}

import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Button from "../../../common/UI/Button";
import Footer from "../../../common/UI/Footer";

export default function LessonsFooter() {
  const navigate = useNavigate();

  return (
    <Footer>
      <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")} className="gap-2">
        <ArrowLeft />
        Back
      </Button>
    </Footer>
  );
}

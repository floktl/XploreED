import React from "react";
import { Target } from "lucide-react";
import Button from "../UI/Button";
import Footer from "../UI/Footer";

export default function VocabularyFooter({ onNavigate }) {
  return (
    <Footer>
      <Button
        variant="primary"
        onClick={() => onNavigate("/vocab-trainer")}
        className="gap-2"
      >
        <Target className="w-4 h-4" />
        Train Vocabulary
      </Button>
    </Footer>
  );
}

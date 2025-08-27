import React from "react";
import { ArrowLeft } from "lucide-react";
import Button from "../UI/Button";
import Footer from "../UI/Footer";

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

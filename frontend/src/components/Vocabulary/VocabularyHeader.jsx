import React from "react";
import { BookOpen, ArrowLeft } from "lucide-react";
import { Title } from "../UI/UI";
import Button from "../UI/Button";

export default function VocabularyHeader({ onNavigate, darkMode }) {
  return (
    <div className="flex justify-between items-center mb-6">
      <Title>
        <div className="flex items-center gap-2">
          <BookOpen className="w-6 h-6" />
          <span>My Vocabulary</span>
        </div>
      </Title>
      <Button
        size="md"
        variant="ghost"
        type="button"
        onClick={() => onNavigate("/menu")}
        className="gap-2"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </Button>
    </div>
  );
}

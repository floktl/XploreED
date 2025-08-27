import React from "react";
import { Book, Target, BrainCircuit } from "lucide-react";
import Button from "../UI/Button";
import Card from "../UI/Card";

export default function ProfileActions({ onNavigate }) {
  return (
    <Card className="mb-6">
      <div className="flex flex-col gap-4">
        <Button
          type="button"
          variant="primary"
          onClick={() => onNavigate("/vocabulary")}
          className="justify-start gap-3"
        >
          <Book className="w-5 h-5" />
          My Vocabulary
        </Button>
        <Button
          type="button"
          variant="primary"
          onClick={() => onNavigate("/progress-test")}
          className="justify-start gap-3"
        >
          <Target className="w-5 h-5" />
          Progress Test
        </Button>
        <Button
          type="button"
          variant="primary"
          onClick={() => onNavigate("/topic-memory")}
          className="justify-start gap-3"
        >
          <BrainCircuit className="w-5 h-5" />
          Topic Memory
        </Button>
      </div>
    </Card>
  );
}

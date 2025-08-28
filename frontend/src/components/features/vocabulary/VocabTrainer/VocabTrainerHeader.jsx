import { Target } from "lucide-react";
import { Title } from "../../../common/UI/UI";

export default function VocabTrainerHeader() {
  return (
    <Title>
      <div className="flex items-center gap-2">
        <Target className="w-6 h-6" />
        <span>Train Vocabulary</span>
      </div>
    </Title>
  );
}

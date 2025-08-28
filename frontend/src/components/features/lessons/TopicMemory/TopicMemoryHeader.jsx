import { Brain } from "lucide-react";
import { Title } from "../../../common/UI/UI";

export default function TopicMemoryHeader() {
  return (
    <Title>
      <div className="flex items-center gap-2">
        <Brain className="w-6 h-6" />
        Topic Memory
      </div>
    </Title>
  );
}

import { MoveRight } from "lucide-react";
import Button from "../../../common/UI/Button";

export default function LevelGameControls({
  onSubmit,
  onNext,
  isAnimating
}) {
  return (
    <div className="max-w-xl mx-auto flex flex-col sm:flex-row gap-4 justify-end">
      <Button variant="primary" type="button" onClick={onSubmit} className="w-full sm:w-auto">
        Submit
      </Button>
      <Button
        variant="ghost"
        type="button"
        onClick={onNext}
        disabled={isAnimating}
        className="flex items-center gap-2 w-full sm:w-auto"
      >
        Next
        <MoveRight />
      </Button>
    </div>
  );
}

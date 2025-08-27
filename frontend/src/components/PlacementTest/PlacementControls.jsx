import React from "react";
import Button from "../UI/Button";

export default function PlacementControls({ onNext }) {
  return (
    <div className="flex gap-4 justify-end max-w-xl mx-auto">
      <Button variant="primary" type="button" onClick={onNext}>
        Next
      </Button>
    </div>
  );
}

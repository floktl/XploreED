import React from "react";
import Card from "../UI/Card";
import Button from "../UI/Button";

const LEVEL_MAP = {
  A1: 0,
  A2: 2,
  B1: 4,
  B2: 6,
  C1: 8,
  C2: 10,
};

export default function LevelSelector({ selected, onLevelSelect, onConfirm }) {
  return (
    <Card className="space-y-4 p-4">
      <div className="grid grid-cols-3 gap-2">
        {Object.keys(LEVEL_MAP).map((lvl) => (
          <Button
            key={lvl}
            type="button"
            variant={selected === lvl ? "primary" : "secondary"}
            onClick={() => onLevelSelect(lvl)}
          >
            {lvl}
          </Button>
        ))}
      </div>
      <Button variant="success" onClick={onConfirm} disabled={!selected}>
        Continue
      </Button>
    </Card>
  );
}

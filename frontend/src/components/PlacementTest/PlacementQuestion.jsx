import React from "react";
import Card from "../UI/Card";
import { Input } from "../UI/UI";

export default function PlacementQuestion({ index, scrambled, answer, setAnswer }) {
  return (
    <Card className="mb-6 p-4">
      <p className="mb-2">Question {index + 1} of 10</p>
      <p className="mb-4">Arrange the words into a correct sentence:</p>
      <div className="mb-4 font-mono">{scrambled.join(" ")}</div>
      <Input
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        placeholder="Type your answer"
      />
    </Card>
  );
}

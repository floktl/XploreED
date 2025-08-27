import React from "react";
import { Title } from "../UI/UI";

export default function LevelGameHeader({ username }) {
  return (
    <Title className="text-3xl font-bold mb-4">
      {username ? `${username}'s` : "Your"} Sentence Order Game 🧩
    </Title>
  );
}

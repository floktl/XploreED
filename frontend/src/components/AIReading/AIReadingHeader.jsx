import React from "react";
import { BookOpen } from "lucide-react";
import { Title } from "../UI/UI";

export default function AIReadingHeader({ title = "AI Reading Exercise" }) {
  return (
    <Title className="">
      <div className="flex items-center gap-2">
        <BookOpen className="w-6 h-6" />
        <span>{title}</span>
      </div>
    </Title>
  );
}

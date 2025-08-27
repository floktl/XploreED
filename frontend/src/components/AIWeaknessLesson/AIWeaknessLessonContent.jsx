import React from "react";
import Card from "../UI/Card";

export default function AIWeaknessLessonContent({ html, error }) {
  if (error) {
    return <p className="text-red-600">{error}</p>;
  }

  return (
    <Card>
      <div className="lesson-content prose dark:prose-invert" dangerouslySetInnerHTML={{ __html: html }} />
    </Card>
  );
}

import React from "react";
import { Container } from "../UI/UI";
import Card from "../UI/Card";
import { Input } from "../UI/UI";
import Button from "../UI/Button";
import Footer from "../UI/Footer";
import AIExerciseBlock from "../AIExerciseBlock";
import LevelUpTestHeader from "./LevelUpTestHeader";

export default function LevelUpTestStages({
  stage,
  data,
  orderAnswer,
  setOrderAnswer,
  translation,
  setTranslation,
  readingAns,
  setReadingAns,
  onStageComplete,
  onNextStage,
  onSubmit,
  actions,
  darkMode
}) {
  if (stage === 0) {
    return (
      <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
        <Container className="pb-20">
          <LevelUpTestHeader title="AI Exercises" />
          <AIExerciseBlock
            data={data.exercise_block}
            blockId="progress"
            onComplete={() => onStageComplete(0)}
            setFooterActions={onStageComplete}
          />
        </Container>
        <Footer>
          <div className="flex gap-2">{actions}</div>
        </Footer>
      </div>
    );
  }

  if (stage === 1) {
    return (
      <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
        <Container className="pb-20">
          <LevelUpTestHeader title="Sentence Ordering" />
          <Card className="space-y-4 p-4">
            <p className="font-mono">{data.scrambled.join(" ")}</p>
            <Input
              value={orderAnswer}
              onChange={(e) => setOrderAnswer(e.target.value)}
              placeholder="Type the correct sentence"
            />
          </Card>
        </Container>
        <Footer>
          <div className="flex gap-2">
            {actions}
            <Button
              variant="primary"
              size="sm"
              className="rounded-full"
              onClick={() => onNextStage(2)}
            >
              Next
            </Button>
          </div>
        </Footer>
      </div>
    );
  }

  if (stage === 2) {
    return (
      <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
        <Container className="pb-20">
          <LevelUpTestHeader title="Translate" />
          <Card className="space-y-4 p-4">
            <p>{data.english}</p>
            <Input
              value={translation}
              onChange={(e) => setTranslation(e.target.value)}
              placeholder="German translation"
            />
          </Card>
        </Container>
        <Footer>
          <div className="flex gap-2">
            {actions}
            <Button
              variant="primary"
              size="sm"
              className="rounded-full"
              onClick={() => onNextStage(3)}
            >
              Next
            </Button>
          </div>
        </Footer>
      </div>
    );
  }

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container className="pb-20">
        <LevelUpTestHeader title="Reading Exercise" />
        <Card className="space-y-4 p-4">
          <p>{data.reading.text}</p>
          {data.reading.questions.map((q) => (
            <div key={q.id} className="space-y-2">
              <p className="font-medium">{q.question}</p>
              {q.options.map((opt) => (
                <Button
                  key={opt}
                  type="button"
                  variant={readingAns[q.id] === opt ? "primary" : "secondary"}
                  onClick={() => setReadingAns({ ...readingAns, [q.id]: opt })}
                >
                  {opt}
                </Button>
              ))}
            </div>
          ))}
        </Card>
      </Container>
      <Footer>
        <div className="flex gap-2">
          {actions}
          <Button
            variant="success"
            size="sm"
            className="rounded-full"
            onClick={onSubmit}
          >
            Submit Test
          </Button>
        </div>
      </Footer>
    </div>
  );
}

import React from "react";
import Button from "./UI/Button";
import Card from "./UI/Card";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";
import useAppStore from "../store/useAppStore";
import diffWords from "../utils/diffWords";

export default function PlacementFeedback({ summary, onDone }) {
  const darkMode = useAppStore((s) => s.darkMode);
  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title className="mb-4 text-3xl font-bold">Placement Test Feedback</Title>
        <Card className="p-4 space-y-4">
          {summary && (
            <div>
              <p className="font-medium mb-2">You answered {summary.correct} of {summary.total} questions correctly.</p>
              {summary.mistakes && summary.mistakes.length > 0 && (
                <div className="text-sm">
                  <p className="font-semibold">Mistakes</p>
                  <ul className="list-disc pl-5 space-y-1">
                    {summary.mistakes.map((m, i) => (
                      <li key={i}>
                        <span className="font-medium">{m.question}</span> – {diffWords(m.your_answer, m.correct_answer)}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </Card>
        <div className="text-center mt-6">
          <Button variant="primary" type="button" onClick={onDone}>Continue</Button>
        </div>
      </Container>
      <Footer />
    </div>
  );
}

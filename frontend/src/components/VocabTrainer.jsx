import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getNextVocabCard, submitVocabAnswer } from "../api";
import Button from "./UI/Button";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";
import useAppStore from "../store/useAppStore";

export default function VocabTrainer() {
  const [card, setCard] = useState(null);
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(true);
  const username = useAppStore((state) => state.username);
  const darkMode = useAppStore((state) => state.darkMode);
  const navigate = useNavigate();

  useEffect(() => {
    loadCard();
  }, []);

  const loadCard = async () => {
    setLoading(true);
    try {
      const data = await getNextVocabCard();
      setCard(data && data.id ? data : null);
      setShow(false);
    } catch {
      setCard(null);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = async (quality) => {
    if (!card) return;
    await submitVocabAnswer(card.id, quality);
    loadCard();
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
    <Container>
        <Title>🎯 Train Vocabulary</Title>
        {loading ? (
          <Alert type="info">Loading...</Alert>
        ) : !card ? (
          <Alert type="success">No cards due right now!</Alert>
        ) : (
          <Card className="text-center space-y-4">
            <p className="text-2xl font-semibold">
              {card.article ? `${card.article} ${card.vocab}` : card.vocab}
            </p>
            {show ? (
              <p className="mb-4">{card.translation}</p>
            ) : (
              <Button onClick={() => setShow(true)} variant="secondary">
                Show Translation
              </Button>
            )}
            {show && (
              <div className="flex justify-center gap-4">
                <Button variant="success" onClick={() => handleAnswer(5)}>
                  I knew it
                </Button>
                <Button variant="danger" onClick={() => handleAnswer(2)}>
                  I forgot
                </Button>
              </div>
            )}
          </Card>
        )}
        <div className="mt-6 text-center">
          <Button variant="link" onClick={() => navigate("/vocabulary")}>⬅️ Back to Vocabulary</Button>
        </div>
      </Container>
      <Footer />
    </div>
  );
}

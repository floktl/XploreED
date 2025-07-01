import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container, Title } from "./UI/UI";
import Card from "./UI/Card";
import Button from "./UI/Button";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";
import { setUserLevel } from "../api";

const LEVEL_MAP: Record<string, number> = {
  A1: 0,
  A2: 2,
  B1: 4,
  B2: 6,
  C1: 8,
  C2: 10,
};

export default function LevelGuess() {
  const [selected, setSelected] = useState<string>("");
  const navigate = useNavigate();
  const darkMode = useAppStore((s) => s.darkMode);
  const setCurrentLevel = useAppStore((s) => s.setCurrentLevel);

  const handleConfirm = async () => {
    if (!selected) return;
    const levelVal = LEVEL_MAP[selected];
    try {
      await setUserLevel(levelVal);
      setCurrentLevel(levelVal);
    } catch (e) {
      console.error("[LevelGuess] failed to set level", e);
    }
    navigate("/menu");
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>\
      <Container>
        <Title>Choose Your Level</Title>
        <Card className="space-y-4 p-4">
          <div className="grid grid-cols-3 gap-2">
            {Object.keys(LEVEL_MAP).map((lvl) => (
              <Button
                key={lvl}
                type="button"
                variant={selected === lvl ? "primary" : "secondary"}
                onClick={() => setSelected(lvl)}
              >
                {lvl}
              </Button>
            ))}
          </div>
          <Button variant="success" onClick={handleConfirm} disabled={!selected}>
            Continue
          </Button>
        </Card>
      </Container>
      <Footer />
    </div>
  );
}

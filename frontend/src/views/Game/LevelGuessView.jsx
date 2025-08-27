import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "../components/UI/UI";
import Footer from "../components/UI/Footer";
import useAppStore from "../store/useAppStore";
import { setUserLevel } from "../api";
import {
	LevelGuessHeader,
	LevelSelector
} from "../components/LevelGuess";

const LEVEL_MAP = {
	A1: 0,
	A2: 2,
	B1: 4,
	B2: 6,
	C1: 8,
	C2: 10,
};

export default function LevelGuessView() {
	const [selected, setSelected] = useState("");
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
		<div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
			<Container>
				<LevelGuessHeader />
				<LevelSelector
					selected={selected}
					onLevelSelect={setSelected}
					onConfirm={handleConfirm}
				/>
			</Container>
			<Footer />
		</div>
	);
}

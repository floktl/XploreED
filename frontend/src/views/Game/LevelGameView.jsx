import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "../components/UI/UI";
import Card from "../components/UI/Card";
import useAppStore from "../store/useAppStore";
import { fetchLevelData, submitLevelAnswer, getUserLevel } from "../api";
import axios from "axios";
import {
  LevelGameHeader,
  LevelGameInstructions,
  LevelGameWords,
  LevelGameInput,
  LevelGameStatus,
  LevelGameFeedback,
  LevelGameControls,
  LevelGameFooter
} from "../components/LevelGame";

export default function LevelGameView() {
  const [level, setLevel] = useState(0);
  const [scrambled, setScrambled] = useState([]);
  const [currentOrder, setCurrentOrder] = useState([]);
  const [sentence, setSentence] = useState("");
  const [typedAnswer, setTypedAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [draggedItem, setDraggedItem] = useState(null);
  const [hoverIndex, setHoverIndex] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState("");
  const [isAnimating, setIsAnimating] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const containerRef = useRef(null);

  const username = useAppStore((state) => state.username);
  const darkMode = useAppStore((state) => state.darkMode);
  const setCurrentLevel = useAppStore((state) => state.setCurrentLevel);
  const addBackgroundActivity = useAppStore((s) => s.addBackgroundActivity);
  const removeBackgroundActivity = useAppStore((s) => s.removeBackgroundActivity);
  const navigate = useNavigate();

  // ElevenLabs API Key - replace with your actual key
  const ELEVENLABS_API_KEY = "sk_7ee62fb46781e4c799b9e0e0ea2d48e2fce51b431bd3d8a8";

  useEffect(() => {
    const loadLevel = async () => {
      try {
        const data = await getUserLevel();
        if (data.level !== undefined) {
          setLevel(data.level);
          setCurrentLevel(data.level);
        }
      } catch (e) {
        console.error("[LevelGame] failed to load user level", e);
      }
    };
    loadLevel();
  }, []);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchLevelData(level);
        if (!data || !Array.isArray(data.scrambled)) {
          throw new Error("Invalid data format");
        }
        setScrambled(data.scrambled);
        setCurrentOrder([...data.scrambled]);
        setSentence(data.sentence || "");
        setFeedback(null);
        setTypedAnswer("");
      } catch (err) {
        console.error("[LevelGame] Failed to load level data:", err);
        setScrambled([]);
        setCurrentOrder([]);
      }
    };

    loadData();
  }, [level]);

  const startRecording = async () => {
    try {
      setTypedAnswer("");
      setStatus("Starting microphone...");

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true
        }
      });

      setStatus("Recording... Speak in German");
      audioChunksRef.current = [];
      setIsRecording(true);

      mediaRecorderRef.current = new MediaRecorder(stream);

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        try {
          if (audioChunksRef.current.length === 0) {
            throw new Error("No audio recorded");
          }

          const audioBlob = new Blob(audioChunksRef.current);
          await processAudio(audioBlob);
        } catch (error) {
          setStatus(`Error: ${error.message}`);
        } finally {
          stream.getTracks().forEach(track => track.stop());
        }
      };

      mediaRecorderRef.current.start(100);

      setTimeout(() => {
        if (isRecording) {
          stopRecording();
        }
      }, 10000);

    } catch (error) {
      setStatus(`Error: ${error.message}`);
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setStatus("Processing German audio...");
    }
  };

  const processAudio = async (audioBlob) => {
    try {
      if (audioBlob.size < 2000) {
        throw new Error("Audio too short - please speak for at least 2 seconds");
      }

      const audioFile = new File([audioBlob], 'recording.webm', {
        type: 'audio/webm',
        lastModified: Date.now()
      });

      const formData = new FormData();
      formData.append('file', audioFile);
      formData.append('model_id', 'scribe_v1');
      formData.append('language', 'de');
      formData.append('punctuation', 'false');

      setStatus("Sending to ElevenLabs...");
      const response = await axios.post(
        'https://api.elevenlabs.io/v1/speech-to-text',
        formData,
        {
          headers: {
            'xi-api-key': ELEVENLABS_API_KEY,
            'Content-Type': 'multipart/form-data'
          },
          timeout: 20000
        }
      );

      if (response.data?.text) {
        let cleanedText = response.data.text.trim();
        cleanedText = cleanedText.replace(/[.,;]+$/, '');

        setTypedAnswer(cleanedText);
        setStatus("German transcription complete");
      } else {
        throw new Error("No text in response");
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail?.message ||
        error.response?.data?.message ||
        error.message;
      setStatus(`API Error: ${errorMsg}`);
      console.error('API Error:', error.response?.data);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleDragStart = (e, index) => {
    e.dataTransfer.setData("text/plain", index);
    setDraggedItem(index);
    e.currentTarget.classList.add("dragging");
    setTimeout(() => {
      e.currentTarget.classList.add("invisible");
    }, 0);
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    setHoverIndex(index);
  };

  const handleDragEnd = (e) => {
    e.currentTarget.classList.remove("dragging", "invisible");
    setDraggedItem(null);
    setHoverIndex(null);
  };

  const handleDrop = (e, dropIndex) => {
    e.preventDefault();
    const dragIndex = Number(e.dataTransfer.getData("text/plain"));

    if (dragIndex !== dropIndex) {
      const newOrder = [...currentOrder];
      const [removed] = newOrder.splice(dragIndex, 1);
      newOrder.splice(dropIndex, 0, removed);
      setCurrentOrder(newOrder);
    }
    setHoverIndex(null);
  };

  const handleTouchStart = (e, index) => {
    setDraggedItem(index);
    const element = e.currentTarget;
    element.classList.add("dragging");
    setTimeout(() => {
      element.classList.add("invisible");
    }, 0);
  };

  const handleTouchMove = (e) => {
    if (draggedItem === null) return;
    e.preventDefault();

    const touch = e.touches[0];
    const elements = document.elementsFromPoint(touch.clientX, touch.clientY);
    const wordElement = elements.find(el => el.classList.contains('word-item'));

    if (wordElement) {
      const index = Number(wordElement.dataset.index);
      setHoverIndex(index);
    }
  };

  const handleTouchEnd = (e) => {
    if (draggedItem === null) return;

    const element = document.querySelector('.word-item.dragging');
    if (element) {
      element.classList.remove("dragging", "invisible");
    }

    if (hoverIndex !== null && draggedItem !== hoverIndex) {
      const newOrder = [...currentOrder];
      const [removed] = newOrder.splice(draggedItem, 1);
      newOrder.splice(hoverIndex, 0, removed);
      setCurrentOrder(newOrder);
    }

    setDraggedItem(null);
    setHoverIndex(null);
  };

  const handleSubmit = async () => {
    try {
      const answer = typedAnswer.trim() || currentOrder.join(" ");

      const vocabActivityId = `level-vocab-${Date.now()}`;
      addBackgroundActivity({
        id: vocabActivityId,
        label: "Saving vocabulary from game...",
        status: "In progress"
      });

      const result = await submitLevelAnswer(level, answer, sentence);
      setFeedback(result);

      setTimeout(() => removeBackgroundActivity(vocabActivityId), 1200);
    } catch (error) {
      console.error("Submission error:", error);
      setFeedback({
        correct: false,
        feedback: "Failed to submit answer. Please try again.",
        correct_sentence: ""
      });
      const vocabActivityId = `level-vocab-${Date.now()}`;
      addBackgroundActivity({
        id: vocabActivityId,
        label: "Saving vocabulary from game...",
        status: "In progress"
      });
      setTimeout(() => removeBackgroundActivity(vocabActivityId), 1200);
    }
  };

  const handleNextWithAnimation = () => {
    setIsAnimating(true);
    setTimeout(() => {
      setIsAnimating(false);
      setSentence("");
      setLevel((prev) => (prev + 1) % 10);
    }, 400);
  };

  return (
    <div
      className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}
      ref={containerRef}
    >
      <Container>
        <LevelGameHeader username={username} />

        <div className="flex justify-center">
          <Card
            className={`
              w-full max-w-xl mx-auto mb-8 p-6 transition-transform duration-400
              ${isAnimating ? "animate-slide-out" : "animate-slide-in"}
              shadow-lg
            `}
            style={{ minHeight: 320 }}
          >
            <LevelGameInstructions darkMode={darkMode} />

            <LevelGameWords
              currentOrder={currentOrder}
              draggedItem={draggedItem}
              hoverIndex={hoverIndex}
              darkMode={darkMode}
              onDragStart={handleDragStart}
              onDragOver={handleDragOver}
              onDragEnd={handleDragEnd}
              onDrop={handleDrop}
              onTouchStart={handleTouchStart}
              onTouchMove={handleTouchMove}
              onTouchEnd={handleTouchEnd}
            />

            <LevelGameInput
              typedAnswer={typedAnswer}
              setTypedAnswer={setTypedAnswer}
              isRecording={isRecording}
              darkMode={darkMode}
              onToggleRecording={toggleRecording}
              elevenLabsApiKey={ELEVENLABS_API_KEY}
            />

            <LevelGameStatus status={status} />
            <LevelGameFeedback feedback={feedback} />
          </Card>
        </div>

        <LevelGameControls
          onSubmit={handleSubmit}
          onNext={handleNextWithAnimation}
          isAnimating={isAnimating}
        />
      </Container>

      <LevelGameFooter onNavigate={navigate} />
    </div>
  );
}

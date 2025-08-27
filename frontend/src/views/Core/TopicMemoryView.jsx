import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "../components/UI/UI";
import Alert from "../components/UI/Alert";
import useAppStore from "../store/useAppStore";
import { getTopicMemory, clearTopicMemory, getTopicWeaknesses } from "../api";
import {
  TopicMemoryHeader,
  TopicMemoryWeaknesses,
  TopicMemoryFilters,
  TopicMemoryTable,
  TopicMemoryMobileFilters,
  TopicMemoryMobileCards,
  TopicMemoryFooter,
  TopicMemoryClearModal
} from "../components/TopicMemory";

export default function TopicMemoryView() {
  const [topics, setTopics] = useState([]);
  const [showClear, setShowClear] = useState(false);
  const [error, setError] = useState("");
  const [weaknesses, setWeaknesses] = useState([]);
  const [filters, setFilters] = useState({
    grammar: "",
    topic: "",
    skill: "",
    context: "",
  });
  const [expandedCard, setExpandedCard] = useState(null);
  const username = useAppStore((state) => state.username);
  const setUsername = useAppStore((state) => state.setUsername);
  const darkMode = useAppStore((state) => state.darkMode);
  const isAdmin = useAppStore((state) => state.isAdmin);
  const navigate = useNavigate();
  const isLoading = useAppStore((state) => state.isLoading);
  const setCurrentPageContent = useAppStore((s) => s.setCurrentPageContent);
  const clearCurrentPageContent = useAppStore((s) => s.clearCurrentPageContent);

  useEffect(() => {
    const storedUsername = localStorage.getItem("username");
    if (!username && storedUsername) {
      setUsername(storedUsername);
    }

    if (!isLoading && (!username || isAdmin)) {
      navigate(isAdmin ? "/admin-panel" : "/");
    }
  }, [isAdmin, username, setUsername, navigate]);

  useEffect(() => {
    if (!isAdmin) {
      getTopicMemory()
        .then((data) => {
          if (Array.isArray(data)) {
            setTopics(data);
          } else if (data && Array.isArray(data.topics)) {
            setTopics(data.topics);
          } else {
            console.warn("Unexpected topic memory data format:", data);
            setTopics([]);
          }
        })
        .catch((err) => {
          console.error("Failed to load topic memory:", err);
          setTopics([]);
        });
    }
  }, [username, isAdmin]);

  useEffect(() => {
    if (isAdmin) return;
    getTopicWeaknesses()
      .then((data) => {
        if (Array.isArray(data)) {
          setWeaknesses(data);
        } else if (data && Array.isArray(data.weaknesses)) {
          setWeaknesses(data.weaknesses);
        } else {
          console.warn("Unexpected weaknesses data format:", data);
          setWeaknesses([]);
        }
      })
      .catch((err) => {
        console.error("Failed to load weaknesses:", err);
        setWeaknesses([]);
      });
  }, [isAdmin]);

  useEffect(() => {
    setCurrentPageContent({
      type: "topic-memory",
      username,
      topics
    });
    return () => clearCurrentPageContent();
  }, [username, topics, setCurrentPageContent, clearCurrentPageContent]);

  const handleClear = async () => {
    try {
      await clearTopicMemory();
      setTopics([]);
      setWeaknesses([]);
      setShowClear(false);
      setError("");
    } catch (err) {
      console.error("Failed to clear topic memory:", err);
      setError("Could not clear topic memory.");
    }
  };

  // Compute unique filter options
  const grammarOptions = ["", ...Array.from(new Set((topics || []).map(t => t.grammar).filter(Boolean)))];
  const topicOptions = ["", ...Array.from(new Set((topics || []).map(t => t.topic).filter(Boolean)))];
  const skillOptions = ["", ...Array.from(new Set((topics || []).map(t => t.skill_type).filter(Boolean)))];
  const contextOptions = ["", ...Array.from(new Set((topics || []).map(t => t.context).filter(Boolean)))];

  // Filter logic: exact match or 'All'
  const filteredTopics = (topics || []).filter((t) =>
    (filters.grammar === "" || t.grammar === filters.grammar) &&
    (filters.topic === "" || t.topic === filters.topic) &&
    (filters.skill === "" || t.skill_type === filters.skill) &&
    (filters.context === "" || t.context === filters.context)
  );

  // Helper: interpolate color from red to yellow to green
  function getUrgencyColor(percent) {
    if (percent <= 50) {
      const ratio = percent / 50;
      return interpolateColor("#EF4444", "#FACC15", ratio);
    } else {
      const ratio = (percent - 50) / 50;
      return interpolateColor("#FACC15", "#22C55E", ratio);
    }
  }

  // Simple hex color interpolation
  function interpolateColor(a, b, t) {
    const ah = a.replace('#', '');
    const bh = b.replace('#', '');
    const ar = parseInt(ah.substring(0,2), 16), ag = parseInt(ah.substring(2,4), 16), ab = parseInt(ah.substring(4,6), 16);
    const br = parseInt(bh.substring(0,2), 16), bg = parseInt(bh.substring(2,4), 16), bb = parseInt(bh.substring(4,6), 16);
    const rr = Math.round(ar + (br-ar)*t), rg = Math.round(ag + (bg-ag)*t), rb = Math.round(ab + (bb-ab)*t);
    return `#${rr.toString(16).padStart(2,'0')}${rg.toString(16).padStart(2,'0')}${rb.toString(16).padStart(2,'0')}`;
  }

  // Map ease_factor (1.3–2.5) to 0–100 for color
  function easeToPercent(ease) {
    const min = 1.3, max = 2.5;
    let p = ((ease - min) / (max - min)) * 100;
    p = Math.max(0, Math.min(100, p));
    return p;
  }

  return (
    <div className={`relative min-h-screen pb-20 overflow-x-hidden ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <TopicMemoryHeader />

        <TopicMemoryWeaknesses weaknesses={weaknesses} getUrgencyColor={getUrgencyColor} />

        {(topics || []).length === 0 ? (
          <Alert type="info">No topic memory saved yet.</Alert>
        ) : (
          <>
            {/* Desktop/tablet table view */}
            <TopicMemoryTable filteredTopics={filteredTopics} darkMode={darkMode} />

            {/* Mobile card view */}
            <TopicMemoryMobileFilters
              filters={filters}
              setFilters={setFilters}
              grammarOptions={grammarOptions}
              topicOptions={topicOptions}
              skillOptions={skillOptions}
              contextOptions={contextOptions}
            />
            <TopicMemoryMobileCards
              filteredTopics={filteredTopics}
              expandedCard={expandedCard}
              setExpandedCard={setExpandedCard}
              getUrgencyColor={getUrgencyColor}
              easeToPercent={easeToPercent}
            />
          </>
        )}

        <div className="mt-6 flex justify-center gap-4">
        </div>
      </Container>

      <TopicMemoryFooter
        onNavigate={navigate}
        onResetFilters={() => setFilters({ grammar: "", topic: "", skill: "", context: "" })}
        onShowClear={() => setShowClear(true)}
      />

      <TopicMemoryClearModal
        showClear={showClear}
        onClose={() => setShowClear(false)}
        onClear={handleClear}
        error={error}
      />
    </div>
  );
}

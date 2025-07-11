import React from "react";
import Joyride from "react-joyride";
import useAppStore from "../store/useAppStore";

const steps = [
  {
    target: "body",
    placement: "center",
    title: "Welcome to XplorED!",
    content: (
      <div>
        <h2 className="text-xl font-bold mb-2">Welcome to XplorED!</h2>
        <p className="mb-2">Let's take a quick tour to get you started with learning German in a fun and interactive way.</p>
      </div>
    ),
    disableBeacon: true,
  },
  {
    target: "[data-tour='start-lesson']",
    title: "Start a Lesson",
    content: "Click here to begin your first German lesson.",
    placement: "bottom",
  },
  {
    target: "[data-tour='ai-feedback']",
    title: "AI Feedback",
    content: "Get instant feedback and explanations from our AI as you practice.",
    placement: "top",
  },
  {
    target: "[data-tour='vocab-trainer']",
    title: "Vocabulary Trainer",
    content: "Practice and review your vocabulary here.",
    placement: "top",
  },
  {
    target: "[data-tour='profile']",
    title: "Profile & Progress",
    content: "Track your progress and achievements.",
    placement: "left",
  },
  {
    target: "[data-tour='help']",
    title: "Ask for Help",
    content: "Need help? Click here to contact support or ask the AI.",
    placement: "left",
  },
  {
    target: "body",
    placement: "center",
    title: "You're Ready!",
    content: (
      <div>
        <h2 className="text-xl font-bold mb-2">You're ready to start!</h2>
        <p>Explore and have fun learning German. Viel Erfolg!</p>
      </div>
    ),
  },
];

export default function OnboardingTour() {
  const showOnboarding = useAppStore((s) => s.showOnboarding);
  const setShowOnboarding = useAppStore((s) => s.setShowOnboarding);

  if (!showOnboarding) return null;

  return (
    <Joyride
      steps={steps.map(step => ({ ...step, placement: "auto" }))}
      continuous
      showSkipButton
      showProgress
      disableScrolling={true}
      disableOverlay={false}
      styles={{
        options: {
          zIndex: 10000,
          primaryColor: "#2563eb",
          textColor: "#222",
          backgroundColor: "#fff",
          maxWidth: 300,
          borderRadius: 12,
          padding: "20px",
        },
        tooltip: {
          maxWidth: 300,
          width: "auto",
          wordBreak: "break-word",
          fontSize: "1.05rem",
        },
      }}
      floaterProps={{
        options: {
          preventOverflow: true,
          placement: "auto",
        },
      }}
      spotlightPadding={8}
      offset={16}
      callback={(data) => {
        if (data.status === "finished" || data.status === "skipped") {
          setShowOnboarding(false);
        }
      }}
    />
  );
}

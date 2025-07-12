import React, { useEffect, useState, useRef } from "react";
import Joyride from "react-joyride";
import useAppStore from "../store/useAppStore";
import { useNavigate } from "react-router-dom";

const mainSteps = [
  {
    target: ".onboarding-root",
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
    title: "Go to AI Exercises",
    content: "Now let's check out the AI-powered exercises!",
    placement: "top",
  },
  {
    target: "[data-tour='exercise-block']",
    title: "How Exercises Work",
    content: (
      <div>
        <h2 className="text-lg font-bold mb-2">How to Use the Exercise Block</h2>
        <p>Type your answer for each exercise. After submitting, you'll get instant feedback, explanations, and alternative correct answers. Use this feedback to learn from your mistakes!</p>
      </div>
    ),
    placement: "top",
  },
  {
    target: ".onboarding-root",
    placement: "center",
    title: "Great!",
    content: (
      <div>
        <h2 className="text-xl font-bold mb-2">Keep going!</h2>
        <p>Try another exercise block to reinforce your learning.</p>
      </div>
    ),
  },
];

const vocabStep = [
  {
    target: "[data-tour='vocab-trainer']",
    title: "Vocabulary Trainer",
    content: (
      <div>
        <h2 className="text-lg font-bold mb-2">Spaced Repetition for Vocabulary</h2>
        <p>The vocab trainer uses a science-backed algorithm (SM2) to schedule reviews just before you forget a word. The more you practice, the longer you'll remember!</p>
      </div>
    ),
    placement: "top",
  },
];

const topicStep = [
  {
    target: "[data-tour='profile']",
    title: "Topic Memory",
    content: (
      <div>
        <h2 className="text-lg font-bold mb-2">Grammar & Topic Memory</h2>
        <p>We track your grammar and topic strengths and weaknesses. The platform adapts to help you master tricky areas over time!</p>
      </div>
    ),
    placement: "top",
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
  const onboardingStage = useAppStore((s) => s.onboardingStage);
  const setOnboardingStage = useAppStore((s) => s.setOnboardingStage);
  const onboardingExerciseCount = useAppStore((s) => s.onboardingExerciseCount);
  const navigate = useNavigate();

  const onboardingStepIndex = useAppStore((s) => s.onboardingStepIndex);
  const setOnboardingStepIndex = useAppStore((s) => s.setOnboardingStepIndex);
  const prevOnboardingStage = useAppStore((s) => s.prevOnboardingStage);
  const setPrevOnboardingStage = useAppStore((s) => s.setPrevOnboardingStage);

  // --- Step index state for manual control ---
  const waitingForTarget = useRef(false);

  useEffect(() => {
    if (prevOnboardingStage !== onboardingStage) {
      console.log('[OnboardingTour] Onboarding stage actually changed:', onboardingStage, 'Resetting stepIndex to 0');
      setOnboardingStepIndex(0);
      setPrevOnboardingStage(onboardingStage);
    }
  }, [onboardingStage, prevOnboardingStage, setOnboardingStepIndex, setPrevOnboardingStage]);

  // Helper: check if a step's target exists in the DOM
  const isTargetMounted = (selector) => {
    if (!selector) return false;
    if (selector === "body") return true;
    const found = !!document.querySelector(selector);
    if (!found) {
      console.log(`[OnboardingTour] Target not found: ${selector}`);
    } else {
      console.log(`[OnboardingTour] Target found: ${selector}`);
    }
    return found;
  };

  // Wait for [data-tour='ai-feedback'] and [data-tour='exercise-block'] before advancing to those steps
  useEffect(() => {
    if (!showOnboarding) return;
    let interval;
    let timeout;
    const pollForTarget = (selector, idx) => {
      interval = setInterval(() => {
        if (isTargetMounted(selector)) {
          console.log(`[OnboardingTour] ${selector} found, showing step ${idx}`);
          setOnboardingStepIndex(idx); // Stay on this step, now target is present
          waitingForTarget.current = false;
          clearInterval(interval);
        } else {
          console.log(`[OnboardingTour] Still polling for ${selector} at step ${idx}`);
        }
      }, 100);
    };
    if (
      onboardingStage === "main" &&
      onboardingStepIndex === 2 &&
      !isTargetMounted("[data-tour='ai-feedback']")
    ) {
      waitingForTarget.current = true;
      console.log('[OnboardingTour] Polling for [data-tour=ai-feedback] after 200ms delay...');
      timeout = setTimeout(() => pollForTarget("[data-tour='ai-feedback']", 2), 200);
    } else if (
      onboardingStage === "main" &&
      onboardingStepIndex === 3 &&
      !isTargetMounted("[data-tour='exercise-block']")
    ) {
      waitingForTarget.current = true;
      console.log('[OnboardingTour] Polling for [data-tour=exercise-block] after 200ms delay...');
      timeout = setTimeout(() => pollForTarget("[data-tour='exercise-block']", 3), 200);
    }
    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [onboardingStage, onboardingStepIndex, showOnboarding, setOnboardingStepIndex]);

  useEffect(() => {
    console.log('[OnboardingTour] stepIndex:', onboardingStepIndex);
  }, [onboardingStepIndex]);

  if (!showOnboarding) return null;

  let steps = mainSteps;
  if (onboardingStage === "vocab") steps = vocabStep;
  if (onboardingStage === "topic") steps = topicStep;

  return (
    <Joyride
      steps={steps.map(step => ({ ...step, placement: "auto" }))}
      stepIndex={onboardingStepIndex}
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
        console.log('[OnboardingTour] Joyride callback:', data);
        // Defensive: auto-navigate if target is missing for next step
        const nextStep = steps[data.index + 1];
        if (data.type === "step:after" && nextStep) {
          if (nextStep.target === "[data-tour='start-lesson']") {
            if (!isTargetMounted(nextStep.target)) {
              console.log('[OnboardingTour] Navigating to /menu for start-lesson');
              navigate("/menu");
            }
          }
          if (nextStep.target === "[data-tour='ai-feedback']") {
            if (!isTargetMounted(nextStep.target)) {
              console.log('[OnboardingTour] Navigating to /ai-feedback for ai-feedback');
              navigate("/ai-feedback");
              // Add delay before polling
              setTimeout(() => {
                console.log('[OnboardingTour] Delayed polling for [data-tour=ai-feedback] after navigation');
              }, 200);
            }
          }
          if (nextStep.target === "[data-tour='exercise-block']") {
            if (!isTargetMounted(nextStep.target)) {
              console.log('[OnboardingTour] Navigating to /ai-feedback for exercise-block');
              navigate("/ai-feedback");
              // Add delay before polling
              setTimeout(() => {
                console.log('[OnboardingTour] Delayed polling for [data-tour=exercise-block] after navigation');
              }, 200);
              waitingForTarget.current = true;
              return;
            }
          }
        }
        // Handle stage transitions
        if (data.status === "finished" || data.status === "skipped") {
          if (onboardingStage === "main" && steps === mainSteps) {
            // Only advance to vocab after two exercise blocks are completed
            if (onboardingExerciseCount >= 2) {
              console.log('[OnboardingTour] Advancing to vocab stage');
              setOnboardingStage("vocab");
              setOnboardingStepIndex(0);
              navigate("/vocab-trainer");
            } else {
              // Stay in main onboarding until two blocks are done
              console.log('[OnboardingTour] Not enough exercise blocks, staying in main');
              setOnboardingStage("main");
              setOnboardingStepIndex(0);
              navigate("/ai-feedback");
              setShowOnboarding(true);
            }
          } else if (onboardingStage === "vocab") {
            console.log('[OnboardingTour] Advancing to topic stage');
            setOnboardingStage("topic");
            setOnboardingStepIndex(0);
            navigate("/profile");
          } else {
            console.log('[OnboardingTour] Onboarding complete');
            setShowOnboarding(false);
            setOnboardingStage("done");
          }
        } else if (data.type === "step:after" && !waitingForTarget.current) {
          // Only advance if not waiting for a target
          setOnboardingStepIndex(data.index + 1);
        }
      }}
    />
  );
}

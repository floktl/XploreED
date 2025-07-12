// useAppStore.js
import { create } from "zustand";

const initialDark = JSON.parse(localStorage.getItem("darkMode") || "false");
const initialOnboarding = JSON.parse(localStorage.getItem("showOnboarding") || "true");

const useAppStore = create((set) => ({
    username: null,
    isAdmin: false,
    adminPassword: null,
    darkMode: initialDark,
    currentLevel: 0,
    isLoading: true,
    showOnboarding: initialOnboarding,
    onboardingExerciseCount: 0,
    setOnboardingExerciseCount: (count) => set({ onboardingExerciseCount: count }),
    incrementOnboardingExerciseCount: () => set((state) => ({ onboardingExerciseCount: state.onboardingExerciseCount + 1 })),
    onboardingStage: "main", // 'main', 'vocab', 'topic', 'done'
    setOnboardingStage: (stage) => set({ onboardingStage: stage }),
    onboardingStepIndex: 0,
    setOnboardingStepIndex: (idx) => set({ onboardingStepIndex: idx }),
    prevOnboardingStage: "main",
    setPrevOnboardingStage: (stage) => set({ prevOnboardingStage: stage }),

    setUsername: (username) => set({ username }),
    setIsAdmin: (isAdmin) => set({ isAdmin }),
    setAdminPassword: (adminPassword) => set({ adminPassword }),
    setCurrentLevel: (level) => set({ currentLevel: level }),
    toggleDarkMode: () =>
        set((state) => {
            const val = !state.darkMode;
            localStorage.setItem("darkMode", JSON.stringify(val));
            return { darkMode: val };
        }),
    setDarkMode: (val) => {
        localStorage.setItem("darkMode", JSON.stringify(val));
        set({ darkMode: val });
    },
    setIsLoading: (val) => set({ isLoading: val }),
    setShowOnboarding: (val) => {
        localStorage.setItem("showOnboarding", JSON.stringify(val));
        set({ showOnboarding: val });
    },

    resetStore: () => {
        localStorage.removeItem("username");
        set({
            username: null,
            isAdmin: false,
            isLoading: false,
            adminPassword: null,
            currentLevel: 0,
        });
    },

}));

export default useAppStore;

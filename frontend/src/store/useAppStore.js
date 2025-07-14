// useAppStore.js
import { create } from "zustand";

const initialDark = JSON.parse(localStorage.getItem("darkMode") || "false");

const useAppStore = create((set, get) => ({
    username: null,
    isAdmin: false,
    adminPassword: null,
    darkMode: initialDark,
    currentLevel: 0,
    isLoading: true,
    backgroundActivity: [], // [{id, label, status}]

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
    addBackgroundActivity: (activity) => set((state) => ({
        backgroundActivity: [...state.backgroundActivity, activity],
    })),
    updateBackgroundActivity: (id, updates) => set((state) => ({
        backgroundActivity: state.backgroundActivity.map((a) =>
            a.id === id ? { ...a, ...updates } : a
        ),
    })),
    removeBackgroundActivity: (id) => set((state) => ({
        backgroundActivity: state.backgroundActivity.filter((a) => a.id !== id),
    })),

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

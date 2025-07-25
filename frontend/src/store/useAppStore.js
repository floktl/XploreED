// useAppStore.js
import { create } from "zustand";

const initialDark = JSON.parse(localStorage.getItem("darkMode") || "false");
const initialDebug = JSON.parse(localStorage.getItem("debugEnabled") || "false");

const useAppStore = create((set, get) => ({
    username: null,
    isAdmin: false,
    adminPassword: null,
    darkMode: initialDark,
    debugEnabled: initialDebug,
    currentLevel: 0,
    isLoading: true,
    backgroundActivity: [], // [{id, label, status}]
    currentPageContent: null, // { type: 'exercise'|'lesson'|'feedback', data: ... }
    footerVisible: true,

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
    toggleDebugEnabled: () =>
        set((state) => {
            const val = !state.debugEnabled;
            localStorage.setItem("debugEnabled", JSON.stringify(val));
            return { debugEnabled: val };
        }),
    setDarkMode: (val) => {
        localStorage.setItem("darkMode", JSON.stringify(val));
        set({ darkMode: val });
    },
    setDebugEnabled: (val) => {
        localStorage.setItem("debugEnabled", JSON.stringify(val));
        set({ debugEnabled: val });
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
    setCurrentPageContent: (content) => set({ currentPageContent: content }),
    clearCurrentPageContent: () => set({ currentPageContent: null }),
    setFooterVisible: (visible) => set({ footerVisible: visible }),

    resetStore: () => {
        localStorage.removeItem("username");
        localStorage.removeItem("debugEnabled");
        set({
            username: null,
            isAdmin: false,
            isLoading: false,
            adminPassword: null,
            currentLevel: 0,
            debugEnabled: false,
        });
    },

}));

export default useAppStore;

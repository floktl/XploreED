// useAppStore.js
import { create } from "zustand";

const useAppStore = create((set) => ({
  username: null,
  isAdmin: false,
  adminPassword: null,
  darkMode: false,
  currentLevel: 0,

  setUsername: (username) => set({ username }),
  setIsAdmin: (isAdmin) => set({ isAdmin }),
  setAdminPassword: (adminPassword) => set({ adminPassword }),
  setCurrentLevel: (level) => set({ currentLevel: level }),
  toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),

  resetStore: () =>
    set({
      username: null,
      isAdmin: false,
      adminPassword: null,
      currentLevel: 0,
    }),
}));

export default useAppStore;

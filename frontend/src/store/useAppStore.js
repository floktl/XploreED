// useAppStore.js
import { create } from "zustand";

const useAppStore = create((set) => ({
  username: null,
  isAdmin: false,
  adminPassword: null,
  darkMode: false,
  currentLevel: 0,
  isLoading: true,
  
  setUsername: (username) => set({ username }),
  setIsAdmin: (isAdmin) => set({ isAdmin }),
  setAdminPassword: (adminPassword) => set({ adminPassword }),
  setCurrentLevel: (level) => set({ currentLevel: level }),
  toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
  setIsLoading: (val) => set({ isLoading: val }),

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

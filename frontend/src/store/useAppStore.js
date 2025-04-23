// useAppStore.js
import { create } from "zustand";

const useAppStore = create((set, get) => ({
  username: null,
  isAdmin: false,
  adminPassword: null,
  darkMode: false,
  currentLevel: 0,
  isLoading: true,
  mistakeCount: 0,  // Track number of consecutive mistakes

  setUsername: (username) => set({ username }),
  setIsAdmin: (isAdmin) => set({ isAdmin }),
  setAdminPassword: (adminPassword) => set({ adminPassword }),
  setCurrentLevel: (level) => set({ currentLevel: level }),
  toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
  setIsLoading: (val) => set({ isLoading: val }),

  // Add mistake tracking functions
  addMistake: () => {
    set((state) => ({ mistakeCount: state.mistakeCount + 1 }));
    return get().mistakeCount;
  },

  resetMistakes: () => set({ mistakeCount: 0 }),

  getMistakeCount: () => get().mistakeCount,

  resetStore: () => {
    localStorage.removeItem("username");
    set({
      username: null,
      isAdmin: false,
      isLoading: false,
      adminPassword: null,
      currentLevel: 0,
      mistakeCount: 0,
    });
  },

}));

export default useAppStore;

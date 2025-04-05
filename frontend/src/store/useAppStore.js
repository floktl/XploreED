import { create } from "zustand";

const useAppStore = create((set) => ({
  username: localStorage.getItem("username") || "anonymous",
  setUsername: (name) => {
    localStorage.setItem("username", name);
    set({ username: name });
  },

  adminPassword: null, // 👈 initialize admin password state
  setAdminPassword: (password) => set({ adminPassword: password }), // ✅ comma was missing here

  darkMode: false,
  toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
  currentLevel: 0,
  setCurrentLevel: (level) => set({ currentLevel: level }),

}));

export default useAppStore;

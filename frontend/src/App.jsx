import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import NameInput from "./components/NameInput";
import Menu from "./components/Menu";
import Translator from "./components/Translator";
import LevelGame from "./components/LevelGame";
import Profile from "./components/Profile";
import Vocabulary from "./components/Vocabulary";
import AdminLogin from "./components/AdminLogin";
import AdminDashboard from "./components/AdminDashboard";
import Lessons from "./components/Lessons";
import ProfileStats from "./components/ProfileStats";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<NameInput />} />
        <Route path="/menu" element={<Menu />} />
        <Route path="/translate" element={<Translator />} />
        <Route path="/level-game" element={<LevelGame />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/vocabulary" element={<Vocabulary />} />
        <Route path="/admin" element={<AdminLogin />} />
        <Route path="/admin-panel" element={<AdminDashboard />} />
        <Route path="/Lessons" element={<Lessons />} />
        <Route path="/profile-stats/:username" element={<ProfileStats />} />
      </Routes>
    </BrowserRouter>
  );
}

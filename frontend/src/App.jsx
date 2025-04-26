import React, { useEffect } from "react";
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";

import NameInput from "./components/NameInput";
import Menu from "./components/Menu";
import Translator from "./components/Translator";
import LevelGame from "./components/LevelGame";
import Profile from "./components/Profile";
import Vocabulary from "./components/Vocabulary";
import PronunciationPractice from "./components/PronunciationPractice";
import AdminLogin from "./components/AdminLogin";
import AdminDashboard from "./components/AdminDashboard";
import Lessons from "./components/Lessons";
import ProfileStats from "./components/ProfileStats";
import LessonView from "./components/LessonView";
import LessonEdit from "./components/LessonEdit";

import useAppStore from "./store/useAppStore";
import { getMe, getRole } from "./api";

// ✅ Auth load on start
function AppWrapper() {
  const setUsername = useAppStore((state) => state.setUsername);
  const setIsAdmin = useAppStore((state) => state.setIsAdmin);
  const setIsLoading = useAppStore((state) => state.setIsLoading);

  useEffect(() => {
    const fetchUserAndRole = async () => {
      try {
        const me = await getMe();
        setUsername(me.username);
        const role = await getRole();
        setIsAdmin(role.is_admin);
      } catch (err) {
        console.warn("[App] Not logged in");
        setIsAdmin(false);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserAndRole();
  }, [setUsername, setIsAdmin, setIsLoading]);

  return <RouterProvider router={router} />;
}

// ✅ Route definitions
const router = createBrowserRouter(
  [
    { path: "/", element: <NameInput /> },
    { path: "/menu", element: <Menu /> },
    { path: "/translate", element: <Translator /> },
    { path: "/level-game", element: <LevelGame /> },
    { path: "/profile", element: <Profile /> },
    { path: "/vocabulary", element: <Vocabulary /> },
    { path: "/pronunciation", element: <PronunciationPractice /> },
    { path: "/admin", element: <AdminLogin /> },
	{ path: "/admin-login", element: <AdminLogin /> },
    { path: "/admin-panel", element: <AdminDashboard /> },
    { path: "/lessons", element: <Lessons /> },
    { path: "/lesson/:lessonId", element: <LessonView /> },
    { path: "/profile-stats", element: <ProfileStats /> },
    { path: "/admin/lessons/:id", element: <LessonEdit /> },
  ],
  {
    future: {
      v7_startTransition: true,
      v7_relativeSplatPath: true,
    },
  }
);

export default AppWrapper;

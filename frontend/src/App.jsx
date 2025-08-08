import React, { useEffect } from "react";
import {
  createBrowserRouter,
  RouterProvider,
  useLocation,
} from "react-router-dom";

import NameInput from "./components/NameInput";
import Menu from "./components/Menu";
import Translator from "./components/Translator";
import LevelGame from "./components/LevelGame";
import PlacementTest from "./components/PlacementTest";
import LevelGuess from "./components/LevelGuess";
import Profile from "./components/Profile";
import Vocabulary from "./components/Vocabulary";
import VocabTrainer from "./components/VocabTrainer";
import AdminLogin from "./components/AdminLogin";
import AdminDashboard from "./components/AdminDashboard";
import AdminUserManagement from "./components/AdminUserManagement";
import Lessons from "./components/Lessons";
import ProfileStats from "./components/ProfileStats";
import LessonView from "./components/LessonView";
import LessonEdit from "./components/LessonEdit";
import AIFeedback from "./components/AIFeedback";
import AIFeedbackView from "./components/AIFeedbackView";
import TopicMemory from "./components/TopicMemory";
import GrammarMap from "./components/GrammarMap";
import AIWeaknessLesson from "./components/AIWeaknessLesson";
import AIReading from "./components/AIReading";
import LevelUpTest from "./components/LevelUpTest";
import ErrorPage from "./components/ErrorPage";
import Settings from "./components/Settings";
import TermsOfService from "./components/TermsOfService";
import About from "./components/About";
import Support from "./components/Support";
import AskAiButton from "./components/AskAiButton";
import RootLayout from "./components/RootLayout";

import useAppStore from "./store/useAppStore";
import { getMe, getRole } from "./api";

// ✅ Auth load on start
function AppWrapper() {
  const setUsername = useAppStore((state) => state.setUsername);
  const setIsAdmin = useAppStore((state) => state.setIsAdmin);
  const setIsLoading = useAppStore((state) => state.setIsLoading);
  const darkMode = useAppStore((state) => state.darkMode);

  useEffect(() => {
    const fetchUserAndRole = async () => {
      try {
        const me = await getMe();
        if (me && me.username) {
          setUsername(me.username);
          localStorage.setItem("username", me.username);

          const role = await getRole();
          setIsAdmin(role.is_admin);
        }
      } catch (err) {
        console.warn("[App] Not logged in:", err.message);
        setUsername(null);
        setIsAdmin(false);
        localStorage.removeItem("username");
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserAndRole();
  }, [setUsername, setIsAdmin, setIsLoading]);

    // Apply dark mode to document level
  useEffect(() => {
    const html = document.documentElement;
    const body = document.body;

    if (darkMode) {
      html.classList.add('dark');
      body.classList.add('dark');
      html.style.backgroundColor = '#111827'; // bg-gray-900
      body.style.backgroundColor = '#111827';

      // Set meta theme-color for mobile browsers
      let metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (!metaThemeColor) {
        metaThemeColor = document.createElement('meta');
        metaThemeColor.name = 'theme-color';
        document.head.appendChild(metaThemeColor);
      }
      metaThemeColor.content = '#111827';

      // Set color-scheme meta tag
      let metaColorScheme = document.querySelector('meta[name="color-scheme"]');
      if (!metaColorScheme) {
        metaColorScheme = document.createElement('meta');
        metaColorScheme.name = 'color-scheme';
        document.head.appendChild(metaColorScheme);
      }
      metaColorScheme.content = 'dark';

    } else {
      html.classList.remove('dark');
      body.classList.remove('dark');
      html.style.backgroundColor = '#ffffff'; // bg-white
      body.style.backgroundColor = '#ffffff';

      // Set meta theme-color for mobile browsers
      let metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (!metaThemeColor) {
        metaThemeColor = document.createElement('meta');
        metaThemeColor.name = 'theme-color';
        document.head.appendChild(metaThemeColor);
      }
      metaThemeColor.content = '#ffffff';

      // Set color-scheme meta tag
      let metaColorScheme = document.querySelector('meta[name="color-scheme"]');
      if (!metaColorScheme) {
        metaColorScheme = document.createElement('meta');
        metaColorScheme.name = 'color-scheme';
        document.head.appendChild(metaColorScheme);
      }
      metaColorScheme.content = 'light';
    }
  }, [darkMode]);

  return <RouterProvider router={router} />;
}

// Renders AskAiButton everywhere except login/signup/admin
function AskAiButtonGlobal() {
  const location = useLocation();
  const path = location.pathname;
  if (
    path === "/" ||
    path === "/admin" ||
    path === "/admin-login" ||
    path === "/admin-panel" ||
    path === "/admin-users" ||
    path.startsWith("/admin/")
  ) {
    return null;
  }
  return <AskAiButton />;
}

// ✅ Route definitions
const router = createBrowserRouter(
  [
    // Auth/admin routes outside RootLayout
    { path: "/", element: <NameInput />, errorElement: <ErrorPage /> },
    { path: "/admin", element: <AdminLogin />, errorElement: <ErrorPage /> },
    {
      path: "/admin-login",
      element: <AdminLogin />,
      errorElement: <ErrorPage />,
    },
    {
      path: "/admin-panel",
      element: <AdminDashboard />,
      errorElement: <ErrorPage />,
    },
    {
      path: "/admin-users",
      element: <AdminUserManagement />,
      errorElement: <ErrorPage />,
    },
    // Main app routes with RootLayout
    {
      element: <RootLayout />,
      children: [
        {
          path: "/placement-test",
          element: <PlacementTest />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/select-level",
          element: <LevelGuess />,
          errorElement: <ErrorPage />,
        },
        { path: "/menu", element: <Menu />, errorElement: <ErrorPage /> },
        {
          path: "/translate",
          element: <Translator />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/level-game",
          element: <LevelGame />,
          errorElement: <ErrorPage />,
        },
        { path: "/profile", element: <Profile />, errorElement: <ErrorPage /> },
        {
          path: "/vocabulary",
          element: <Vocabulary />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/topic-memory",
          element: <TopicMemory />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/grammar-map",
          element: <GrammarMap />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/vocab-trainer",
          element: <VocabTrainer />,
          errorElement: <ErrorPage />,
        },
        { path: "/lessons", element: <Lessons />, errorElement: <ErrorPage /> },
        {
          path: "/lesson/:lessonId",
          element: <LessonView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/profile-stats",
          element: <ProfileStats />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/settings",
          element: <Settings />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/support",
          element: <Support />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/admin/lessons/:id",
          element: <LessonEdit />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/ai-feedback",
          element: <AIFeedback />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/ai-feedback/:feedbackId",
          element: <AIFeedbackView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/weakness-lesson",
          element: <AIWeaknessLesson />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/reading-exercise",
          element: <AIReading />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/progress-test",
          element: <LevelUpTest />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/terms-of-service",
          element: <TermsOfService />,
          errorElement: <ErrorPage />,
        },
        { path: "/about", element: <About />, errorElement: <ErrorPage /> },
      ],
    },
  ],
  {
    future: {
      v7_startTransition: true,
      v7_relativeSplatPath: true,
    },
  },
);

export default AppWrapper;

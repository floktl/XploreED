import React, { useEffect } from "react";
import {
  createBrowserRouter,
  RouterProvider,
  useLocation,
} from "react-router-dom";

import NameInput from "./components/NameInput";
import { MenuView, LessonsView, ProfileView, VocabularyView, SettingsView, TranslatorView, VocabTrainerView, SupportView, AboutView, TermsOfServiceView, ProfileStatsView, LevelGuessView, PlacementTestView, LevelUpTestView, GrammarMapView, AIFeedbackView, AIWeaknessLessonView, AIReadingView, LevelGameView, TopicMemoryView } from "./views";

import AdminLogin from "./components/AdminLogin";
import AdminDashboard from "./components/AdminDashboard";
import AdminUserManagement from "./components/AdminUserManagement";
import LessonView from "./components/LessonView";
import LessonEdit from "./components/LessonEdit";


import ErrorPage from "./components/ErrorPage";
import TermsOfService from "./components/TermsOfService";
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
          element: <PlacementTestView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/select-level",
          element: <LevelGuessView />,
          errorElement: <ErrorPage />,
        },
        { path: "/menu", element: <MenuView />, errorElement: <ErrorPage /> },
        {
          path: "/translate",
          element: <TranslatorView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/level-game",
          element: <LevelGameView />,
          errorElement: <ErrorPage />,
        },
        { path: "/profile", element: <ProfileView />, errorElement: <ErrorPage /> },
        {
          path: "/vocabulary",
          element: <VocabularyView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/topic-memory",
          element: <TopicMemoryView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/grammar-map",
          element: <GrammarMapView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/vocab-trainer",
          element: <VocabTrainerView />,
          errorElement: <ErrorPage />,
        },
        { path: "/lessons", element: <LessonsView />, errorElement: <ErrorPage /> },
        {
          path: "/lesson/:lessonId",
          element: <LessonView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/profile-stats",
          element: <ProfileStatsView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/settings",
          element: <SettingsView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/support",
          element: <SupportView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/admin/lessons/:id",
          element: <LessonEdit />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/ai-feedback",
          element: <AIFeedbackView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/ai-feedback/:feedbackId",
          element: <AIFeedbackView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/weakness-lesson",
          element: <AIWeaknessLessonView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/reading-exercise",
          element: <AIReadingView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/progress-test",
          element: <LevelUpTestView />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/terms-of-service",
          element: <TermsOfServiceView />,
          errorElement: <ErrorPage />,
        },
        { path: "/about", element: <AboutView />, errorElement: <ErrorPage /> },
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

import { useEffect } from "react";
import {
  createBrowserRouter,
  RouterProvider,
  useLocation,
} from "react-router-dom";

import { NameInput } from "./components/features/auth";
import { MenuView, LessonsView, LessonView, ProfileView, VocabularyView, SettingsView, TranslatorView, VocabTrainerView, SupportView, AboutView, TermsOfServiceView, ProfileStatsView, LevelGuessView, PlacementTestView, LevelUpTestView, GrammarMapView, AIFeedbackView, AIWeaknessLessonView, AIReadingView, LevelGameView, TopicMemoryView } from "./pages";

import AdminLoginView from "./pages/Core/AdminLoginView";
import { AdminDashboard, AdminUserManagement } from "./components/features/admin";

import LessonEditView from "./pages/Core/LessonEditView";


import ErrorPageView from "./pages/Core/ErrorPageView";
import { AskAiButton } from "./components/features/ai";
import { RootLayout } from "./components/layout";

import useAppStore from "./store/useAppStore";
import { getMe, getRole } from "./services/api";

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
    { path: "/", element: <NameInput />, errorElement: <ErrorPageView /> },
    { path: "/admin", element: <AdminLoginView />, errorElement: <ErrorPageView /> },
    {
      path: "/admin-login",
      element: <AdminLoginView />,
      errorElement: <ErrorPageView />,
    },
    {
      path: "/admin-panel",
      element: <AdminDashboard />,
      errorElement: <ErrorPageView />,
    },
    {
      path: "/admin-users",
      element: <AdminUserManagement />,
      errorElement: <ErrorPageView />,
    },
    // Main app routes with RootLayout
    {
      element: <RootLayout />,
      children: [
        {
          path: "/placement-test",
          element: <PlacementTestView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/select-level",
          element: <LevelGuessView />,
          errorElement: <ErrorPageView />,
        },
        { path: "/menu", element: <MenuView />, errorElement: <ErrorPageView /> },
        {
          path: "/translate",
          element: <TranslatorView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/level-game",
          element: <LevelGameView />,
          errorElement: <ErrorPageView />,
        },
        { path: "/profile", element: <ProfileView />, errorElement: <ErrorPageView /> },
        {
          path: "/vocabulary",
          element: <VocabularyView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/topic-memory",
          element: <TopicMemoryView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/grammar-map",
          element: <GrammarMapView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/vocab-trainer",
          element: <VocabTrainerView />,
          errorElement: <ErrorPageView />,
        },
        { path: "/lessons", element: <LessonsView />, errorElement: <ErrorPageView /> },
        {
          path: "/lesson/:lessonId",
          element: <LessonView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/profile-stats",
          element: <ProfileStatsView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/settings",
          element: <SettingsView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/support",
          element: <SupportView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/admin/lessons/:id",
          element: <LessonEditView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/ai-feedback",
          element: <AIFeedbackView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/ai-feedback/:feedbackId",
          element: <AIFeedbackView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/weakness-lesson",
          element: <AIWeaknessLessonView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/reading-exercise",
          element: <AIReadingView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/progress-test",
          element: <LevelUpTestView />,
          errorElement: <ErrorPageView />,
        },
        {
          path: "/terms-of-service",
          element: <TermsOfServiceView />,
          errorElement: <ErrorPageView />,
        },
        { path: "/about", element: <AboutView />, errorElement: <ErrorPageView /> },
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

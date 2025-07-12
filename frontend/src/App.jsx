import React, { useEffect } from "react";
import {
    createBrowserRouter,
    RouterProvider,
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
import AskAiButton from "./components/AskAiButton";
import TermsOfService from "./components/TermsOfService";
import About from "./components/About";
import RootLayout from "./components/RootLayout";

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

    return (
        <>
            <RouterProvider router={router} />
        </>
    );
}

// ✅ Route definitions
const router = createBrowserRouter(
    [
        {
            element: <RootLayout />,
            errorElement: <ErrorPage />,
            children: [
                { path: "/", element: <NameInput /> },
                { path: "/placement-test", element: <PlacementTest /> },
                { path: "/select-level", element: <LevelGuess /> },
                { path: "/menu", element: <Menu /> },
                { path: "/translate", element: <Translator /> },
                { path: "/level-game", element: <LevelGame /> },
                { path: "/profile", element: <Profile /> },
                { path: "/vocabulary", element: <Vocabulary /> },
                { path: "/topic-memory", element: <TopicMemory /> },
                { path: "/grammar-map", element: <GrammarMap /> },
                { path: "/vocab-trainer", element: <VocabTrainer /> },
                { path: "/admin", element: <AdminLogin /> },
                { path: "/admin-login", element: <AdminLogin /> },
                { path: "/admin-panel", element: <AdminDashboard /> },
                { path: "/admin-users", element: <AdminUserManagement /> },
                { path: "/lessons", element: <Lessons /> },
                { path: "/lesson/:lessonId", element: <LessonView /> },
                { path: "/profile-stats", element: <ProfileStats /> },
                { path: "/settings", element: <Settings /> },
                { path: "/admin/lessons/:id", element: <LessonEdit /> },
                { path: "/ai-feedback", element: <AIFeedback /> },
                { path: "/ai-feedback/:feedbackId", element: <AIFeedbackView /> },
                { path: "/weakness-lesson", element: <AIWeaknessLesson /> },
                { path: "/reading-exercise", element: <AIReading /> },
                { path: "/progress-test", element: <LevelUpTest /> },
                { path: "/terms-of-service", element: <TermsOfService /> },
                { path: "/about", element: <About /> }
            ]
        }
    ],
    {
        future: {
            v7_startTransition: true,
            v7_relativeSplatPath: true,
        },
    }
);

export default AppWrapper;

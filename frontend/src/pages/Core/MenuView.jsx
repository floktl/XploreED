import { useLayoutEffect, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
	FileText,
	Target,
	Book,
	Library,
	Bot,
	BarChart3,
	Brain,
	User,
	Settings,
	GraduationCap,
	BookOpen,
	Gamepad2
} from "lucide-react";

import { Container } from "../../components/common/UI/UI";
import useAppStore from "../../store/useAppStore";
import { getUserLevel, getStudentLessons } from "../../services/api";
import { PageLayout } from "../../components/layout";
import AskAiButton from "../../components/features/ai/AskAiButton/AskAiButton";
import MenuHeader from "../../components/layout/MenuNavigation/MenuHeader";
import MenuSection from "../../components/layout/MenuSections/MenuSection";

export default function MenuView() {
	const navigate = useNavigate();
	const username = useAppStore((state) => state.username);
	const setUsername = useAppStore((state) => state.setUsername);
	const darkMode = useAppStore((state) => state.darkMode);
	const isAdmin = useAppStore((state) => state.isAdmin);
	const isLoading = useAppStore((state) => state.isLoading);
	const debugEnabled = useAppStore((state) => state.debugEnabled);
	const setCurrentLevel = useAppStore((state) => state.setCurrentLevel);
	const setCurrentPageContent = useAppStore((s) => s.setCurrentPageContent);
	const clearCurrentPageContent = useAppStore((s) => s.clearCurrentPageContent);
	const setFooterVisible = useAppStore((s) => s.setFooterVisible);

	const [expandedSections, setExpandedSections] = useState({
		exercises: false,
		learning: false,
		tools: false
	});

	const [notifications, setNotifications] = useState({
		newLessons: 0,
		newWeaknessLessons: 0
	});

	const toggleSection = (section) => {
		setExpandedSections(prev => ({
			...prev,
			[section]: !prev[section]
		}));
	};

	// Check for new content
	const checkForNewContent = async () => {
		if (!username) return;

		try {
			const lessonsData = await getStudentLessons();
			const lessons = lessonsData.lessons || [];

			// Count new lessons - improved logic to detect newly published lessons
			const newLessons = lessons.filter(lesson => {
				// A lesson is considered "new" if:
				// 1. Not completed AND
				// 2. Either:
				//    - Never attempted (last_attempt is null/undefined)
				//    - Has very low progress (less than 10%) and no recent activity
				//    - Was recently published (created_at is within last 7 days)
				const isNotCompleted = !lesson.completed;
				const neverAttempted = !lesson.last_attempt;
				const lowProgress = lesson.percent_complete < 10;
				const recentlyPublished = lesson.created_at &&
					new Date(lesson.created_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000); // Published in last 7 days

				const isNew = isNotCompleted && (neverAttempted || lowProgress || recentlyPublished);

				return isNew;
			}).length;

			// For now, we'll assume weakness lessons are new if they exist
			// In a real app, you'd have a separate API to check weakness lesson status
			const newWeaknessLessons = 1; // Placeholder - replace with actual logic

			setNotifications({
				newLessons,
				newWeaknessLessons
			});
		} catch (error) {
			console.error("Failed to check for new content:", error);
		}
	};

	useLayoutEffect(() => {
		setFooterVisible(false); // No footer on menu
	}, [setFooterVisible]);

	useEffect(() => {
		// If admin, go straight to admin panel and skip student data fetches
		if (isAdmin) {
			navigate("/admin-panel");
			return;
		}
		const storedUsername = localStorage.getItem("username");
		if (!username && storedUsername) {
			setUsername(storedUsername);
		}

		// Only fetch level if we have a username
		if (username && !isLoading) {
			const fetchLevel = async () => {
				try {
					const data = await getUserLevel();
					if (data.level !== undefined) setCurrentLevel(data.level);
				} catch (e) {
					console.error("[Menu] failed to load level", e);
					// If authentication fails, redirect to login
					if (e.message.includes("Failed to fetch user level")) {
						navigate("/");
					}
				}
			};
			fetchLevel();
		}

		if (!isLoading && !username) {
			navigate("/");
		}

		// Check for new content when component mounts
		checkForNewContent();

		setCurrentPageContent({
			type: "menu",
			description: "This is the main menu of the XplorED app. Users can access translation practice, sentence order games, AI training exercises, AI reading exercises, weakness lessons, lessons, and more. Each button navigates to a different learning module.",
			sections: [
				{ label: "Translation Practice", path: "/translate", icon: "FileText" },
				...(debugEnabled ? [{ label: "Sentence Order Game", path: "/level-game", icon: "Target" }] : []),
				{ label: "AI Training Exercises", path: "/ai-feedback", icon: "Bot" },
				{ label: "AI Reading Exercise", path: "/reading-exercise", icon: "Book" },
				{ label: "Weakness Lesson", path: "/weakness-lesson", icon: "Brain" },
				{ label: "Lessons", path: "/lessons", icon: "Library" },
			]
		});
		return () => clearCurrentPageContent();
	}, [username, setUsername, isAdmin, isLoading, navigate, setCurrentLevel, setCurrentPageContent, clearCurrentPageContent, setFooterVisible]);

	// Check for new content periodically
	useEffect(() => {
		const interval = setInterval(checkForNewContent, 10000); // Check every 10 seconds for more responsive updates
		return () => clearInterval(interval);
	}, [username]);

	const menuSections = [
		{
			id: "exercises",
			title: "Exercises & Practice",
			icon: Gamepad2,
			color: "blue",
			items: [
				{
					title: "Translation Practice",
					description: "Practice translating between languages",
					icon: FileText,
					path: "/translate",
					variant: "primary"
				},
				{
					title: "AI Training Exercises",
					description: "Interactive AI-powered learning exercises",
					icon: Bot,
					path: "/ai-feedback",
					variant: "secondary"
				},
				{
					title: "AI Reading Exercise",
					description: "Reading comprehension with AI assistance",
					icon: Book,
					path: "/reading-exercise",
					variant: "secondary"
				},
				...(debugEnabled ? [{
					title: "Sentence Order Game",
					description: "Practice sentence structure and word order",
					icon: Target,
					path: "/level-game",
					variant: "secondary"
				}] : [])
			]
		},
		{
			id: "learning",
			title: "Learning Materials",
			icon: GraduationCap,
			color: "green",
			notifications,
			items: [
				{
					title: "Lessons",
					description: "Structured learning content and courses",
					icon: Library,
					path: "/lessons",
					variant: "primary",
					notification: notifications.newLessons
				},
				{
					title: "Weakness Lessons",
					description: "Targeted lessons for your weak areas",
					icon: Brain,
					path: "/weakness-lesson",
					variant: "secondary",
					notification: notifications.newWeaknessLessons
				}
			]
		},
		{
			id: "tools",
			title: "Tools & Analytics",
			icon: BarChart3,
			color: "purple",
			items: [
				{
					title: "Profile & Stats",
					description: "View your learning progress and achievements",
					icon: User,
					path: "/profile",
					variant: "secondary"
				},
				{
					title: "Vocabulary",
					description: "Manage and review your vocabulary",
					icon: BookOpen,
					path: "/vocabulary",
					variant: "secondary"
				},
				{
					title: "Settings",
					description: "Customize your learning experience",
					icon: Settings,
					path: "/settings",
					variant: "secondary"
				}
			]
		}
	];

	const getColorClasses = (color) => {
		const colors = {
			blue: {
				bg: "bg-gray-50/50 dark:bg-gray-800/30",
				border: "border-gray-200 dark:border-gray-700",
				text: "text-gray-900 dark:text-gray-100",
				icon: "text-gray-600 dark:text-gray-300"
			},
			green: {
				bg: "bg-gray-50/50 dark:bg-gray-800/30",
				border: "border-gray-200 dark:border-gray-700",
				text: "text-gray-900 dark:text-gray-100",
				icon: "text-gray-600 dark:text-gray-300"
			},
			purple: {
				bg: "bg-gray-50/50 dark:bg-gray-800/30",
				border: "border-gray-200 dark:border-gray-700",
				text: "text-gray-900 dark:text-gray-100",
				icon: "text-gray-600 dark:text-gray-300"
			}
		};
		return colors[color] || colors.blue;
	};

	return (
		<PageLayout variant="relative">
			<Container>
				<MenuHeader username={username} level={3} />
				{menuSections.map((section) => (
					<MenuSection
						key={section.id}
						section={section}
						expandedSections={expandedSections}
						toggleSection={toggleSection}
						darkMode={darkMode}
						getColorClasses={getColorClasses}
					/>
				))}
			</Container>
			<AskAiButton />
		</PageLayout>
	);
}

import React, { useLayoutEffect, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
	FileText,
	Target,
	Book,
	Library,
	Bot,
	BarChart3,
	Brain,
	ChevronRight,
	ChevronDown,
	User,
	Settings,
	Trophy,
	GraduationCap,
	Zap,
	Lightbulb,
	BookOpen,
	Gamepad2
} from "lucide-react";

import Button from "./UI/Button";
import Card from "./UI/Card";
import Footer from "./UI/Footer";
import { Container, Title } from "./UI/UI";
import useAppStore from "../store/useAppStore";
import { getUserLevel, getStudentLessons } from "../api";
import AskAiButton from "./AskAiButton";

export default function Menu() {
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
		exercises: true,
		learning: true,
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
		<div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
			<Container>
				{/* Modern Header */}
				<div className="mb-8">
					<div className="flex items-center justify-between">
						<div>
							<h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
								Welcome back
							</h1>
							<p className={`text-base font-medium text-gray-600 dark:text-gray-300 mt-1`}>
								{username}
							</p>
						</div>
						<div className={`px-3 py-1.5 rounded-full text-sm font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700`}>
							Level 3
						</div>
					</div>
				</div>

				{/* Modern Menu Grid */}
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
					{menuSections.map((section) => {
						const colors = getColorClasses(section.color);
						const isExpanded = expandedSections[section.id];

						return (
							<div key={section.id} className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm">
								<div className="p-6">
									{/* Modern Section Header */}
									<button
										onClick={() => toggleSection(section.id)}
										className="w-full flex items-center justify-between p-0 hover:opacity-80 transition-opacity"
									>
										<div className="flex items-center space-x-3">
											<div className={`p-2 rounded-xl bg-gray-100 dark:bg-gray-700`}>
												<section.icon className={`w-5 h-5 ${colors.icon}`} />
											</div>
											<div className="flex items-center space-x-2">
												<h2 className={`text-lg font-semibold ${colors.text}`}>
													{section.title}
												</h2>
												{section.id === "learning" && (notifications.newLessons > 0 || notifications.newWeaknessLessons > 0) && (
													<div className="flex-shrink-0">
														<div className="bg-red-500 text-white text-xs font-medium px-2 py-1 rounded-full min-w-[20px] text-center">
															{notifications.newLessons + notifications.newWeaknessLessons > 99 ? '99+' : notifications.newLessons + notifications.newWeaknessLessons}
														</div>
													</div>
												)}
											</div>
										</div>
										{isExpanded ? (
											<ChevronDown className="w-5 h-5 text-gray-400" />
										) : (
											<ChevronRight className="w-5 h-5 text-gray-400" />
										)}
									</button>

									{/* Modern Section Items */}
									{isExpanded && (
										<div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
											{section.items.map((item, index) => (
												<div
													key={index}
													onClick={() => navigate(item.path)}
													className={`group cursor-pointer p-4 rounded-xl border border-gray-200 dark:border-gray-700 transition-all duration-200 hover:shadow-md hover:border-gray-300 dark:hover:border-gray-600 ${darkMode
															? "bg-gray-800/50 hover:bg-gray-800"
															: "bg-gray-50/50 hover:bg-gray-50"
														}`}
												>
													<div className="flex flex-col space-y-3">
														<div className="flex items-center space-x-3">
															<div className={`p-2.5 rounded-xl ${item.variant === "primary"
																	? "bg-gray-100 dark:bg-gray-700"
																	: "bg-gray-100 dark:bg-gray-700"
																}`}>
																<item.icon className={`w-5 h-5 ${item.variant === "primary"
																		? "text-gray-700 dark:text-gray-300"
																		: "text-gray-600 dark:text-gray-400"
																	}`} />
															</div>
															<div className="min-w-0 flex-1">
																<div className="flex items-center space-x-2">
																	<h3 className="font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
																		{item.title}
																	</h3>
																	{item.notification > 0 && (
																		<div className="flex-shrink-0">
																			<div className="bg-red-500 text-white text-xs font-medium px-2 py-1 rounded-full min-w-[20px] text-center">
																				{item.notification > 99 ? '99+' : item.notification}
																			</div>
																		</div>
																	)}
																</div>
															</div>
														</div>
														<p className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
															{item.description}
														</p>
													</div>
												</div>
											))}
										</div>
									)}
								</div>
							</div>
						);
					})}
				</div>
			</Container>
			<AskAiButton />
		</div>
	);
}

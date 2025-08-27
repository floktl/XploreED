import React from "react";
import { Outlet, useLocation } from "react-router-dom";
import AskAiButton from "./AskAiButton";
import Header from "./UI/Header";
import Footer from "./UI/Footer";

export default function RootLayout() {
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
		return <Outlet />;
	}
	return (
		<div className="min-h-screen flex flex-col bg-white dark:bg-gray-900">
			<Header />
			<main className="flex-1 pt-16 pb-20">
				<Outlet />
				<AskAiButton />
			</main>
			<Footer />
		</div>
	);
}

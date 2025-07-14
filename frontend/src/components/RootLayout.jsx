import React from "react";
import { Outlet, useLocation } from "react-router-dom";
import AskAiButton from "./AskAiButton";

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
    <div className="pt-16">
      <Outlet />
      <AskAiButton />
    </div>
  );
}

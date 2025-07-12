import React from "react";
import { Outlet } from "react-router-dom";
import OnboardingTour from "./OnboardingTour";

export default function RootLayout() {
    return (
        <>
            <Outlet />
            <OnboardingTour />
        </>
    );
}

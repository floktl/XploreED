import React from "react";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";

export default function ErrorPage() {
    return (
        <div className="min-h-screen flex items-center justify-center p-6">
            <Container>
                <Title>Something went wrong</Title>
                <p className="mb-4">An unexpected error occurred. Please try again.</p>
                <div className="text-center">
                    <Button variant="link" onClick={() => window.location.assign("/")}>⬅️ Go Home</Button>
                </div>
            </Container>
        </div>
    );
}

import React from "react";
import { Container, Title } from "./UI/UI";
import Card from "./UI/Card";

export default function About() {
    return (
        <Container>
            <Card>
                <Title>About XplorED</Title>
                <p className="mb-2">XplorED is a platform for learning German.</p>
                <p>
                    Practice vocabulary, grammar and more through interactive
                    exercises and AI-powered lessons.
                </p>
            </Card>
        </Container>
    );
}

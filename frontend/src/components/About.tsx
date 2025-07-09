import React from "react";
import { Container, Title } from "./UI/UI";
import Card from "./UI/Card";

export default function About() {
    return (
        <Container>
            <Card>
                <Title>About XplorED</Title>
                <p className="mb-2">XplorED is a platform for learning German.</p>

                <section className="about-section">
                    <h2>About the Platform</h2>
                    <p>
                        Our mission is to make German learning engaging, effective, and accessible to everyone—whether you're just starting or advancing to B1 and beyond. This platform combines <strong>scientifically-backed language methods</strong> with modern technology to provide a personalized learning journey.
                    </p>

                    <h3><i className="icon-target mr-2" />How It Works</h3>
                    <ul className="space-y-2 list-disc pl-5">
                        <li><strong>Level-based Progression:</strong> The platform adapts to your current CEFR level (A1–B1), guiding you through interactive lessons, quizzes, and challenges that match your skills.</li>
                        <li><strong>AI-Generated Exercises:</strong> Every exercise block is generated using an AI model trained on common learner mistakes, targeting your weaknesses and optimizing your learning curve.</li>
                        <li><strong>Grammar & Vocab Context:</strong> Lessons include grammar notes, real-world examples, and vocabulary highlights within each exercise—no need to switch tabs or look things up.</li>
                        <li><strong>Spaced Repetition (SM2 Algorithm):</strong> Your vocabulary is reviewed automatically using a smart scheduling system to boost long-term retention.</li>
                        <li><strong>Conversation Practice:</strong> Build full German sentences from shuffled word cards to practice syntax and get immediate AI feedback on correctness and fluency.</li>
                    </ul>

                    <h3><i className="icon-brain mr-2" />Features</h3>
                    <div className="feature-grid">
                        <div className="feature-card p-4 shadow rounded">
                            <h4><i className="icon-message-square mr-2" />Smart Feedback</h4>
                            <p>Get instant AI-powered feedback on your answers, including explanations for grammar mistakes, word order issues, or missing articles.</p>
                        </div>
                        <div className="feature-card p-4 shadow rounded">
                            <h4><i className="icon-grid mr-2" />Interactive Sentence Builder</h4>
                            <p>Practice sentence construction with drag-and-drop blocks. Learn word order (SVO, TMP, etc.) visually and intuitively.</p>
                        </div>
                        <div className="feature-card p-4 shadow rounded">
                            <h4><i className="icon-info mr-2" />Visual Grammar Tips</h4>
                            <p>Short pop-up grammar tips appear as you learn, complete with highlight colors, tables, and simplified rules.</p>
                        </div>
                        <div className="feature-card p-4 shadow rounded">
                            <h4><i className="icon-lightbulb mr-2" />Custom AI Lessons</h4>
                            <p>Our AI generates bite-sized grammar or vocabulary lessons based on your weakest topics—perfect for targeted revision or quick refreshers.</p>
                        </div>
                        <div className="feature-card p-4 shadow rounded">
                            <h4><i className="icon-bar-chart mr-2" />Progress Tracking</h4>
                            <p>Your learning stats are tracked in detail: time spent, topics mastered, review intervals, and more—all visualized clearly.</p>
                        </div>
                        <div className="feature-card p-4 shadow rounded">
                            <h4><i className="icon-smartphone mr-2" />Mobile-Friendly</h4>
                            <p>Study anywhere, anytime. The platform is fully responsive and works beautifully on both phones and desktops.</p>
                        </div>
                    </div>

                    <h3><i className="icon-user-check mr-2" />For Teachers & Admins</h3>
                    <p>
                        Teachers can view individual student progress, assign lessons, and get detailed analytics on strengths and weaknesses. Everything runs in real-time with no manual grading required.
                    </p>

                    <blockquote>
                        <p>“This feels like Duolingo—but with actual explanations and real feedback. It’s the most complete German app I’ve tried.”</p>
                        <footer>— Beta user, Level A2</footer>
                    </blockquote>

                    <p className="mt-6">
                        Start your journey today and experience a smarter, friendlier way to learn German.
                    </p>
                </section>
            </Card>
        </Container>
    );
}

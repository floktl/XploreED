import Button from "../../../common/UI/Button";
import Card from "../../../common/UI/Card";
import Footer from "../../../common/UI/Footer";
import { Container, Title } from "../../../common/UI/UI";
import useAppStore from "../../../../store/useAppStore";
import FeedbackSummary from "./Components/FeedbackSummary";

export default function PlacementFeedback({ summary, onDone }) {
    const darkMode = useAppStore((s) => s.darkMode);

    return (
        <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
            <Container
                className="pb-20"
                bottom={
                    <Button variant="primary" type="button" onClick={onDone}>Continue</Button>
                }
            >
                <Title className="mb-4 text-3xl font-bold">Placement Test Feedback</Title>
                <Card className="p-4 space-y-4">
                    <FeedbackSummary summary={summary} />
                </Card>
            </Container>
            <Footer>
                <Button variant="primary" type="button" onClick={onDone}>Continue</Button>
            </Footer>
        </div>
    );
}

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import useAppStore from "../store/useAppStore";
import Card from "./UI/Card";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";
// import your API helper for AI feedback
// import { getAIFeedbackDetail } from "../api";

export default function AIFeedbackView() {
  const { feedbackId } = useParams();
  const [feedback, setFeedback] = useState(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const isAdmin = useAppStore((state) => state.isAdmin);

  useEffect(() => {
    if (isAdmin) {
      navigate("/admin-panel");
      return;
    }

    // const fetchFeedback = async () => {
    //   try {
    //     // Replace with your actual API call
    //     // const data = await getAIFeedbackDetail(feedbackId);
    //     const data = {
    //       id: feedbackId,
    //       title: `Feedback #${feedbackId}`,
    //       content: "This is a sample AI feedback detail.",
    //       created_at: new Date().toISOString(),
    //     };
    //     setFeedback(data);
    //   } catch (err) {
    //     setError("Could not load feedback.");
    //   }
    // };

    // Mocked data

    const fetchFeedback = async () => {
      try {
        // Read all feedback from localStorage
        const allFeedback = JSON.parse(
          localStorage.getItem("aiFeedback") || "[]"
        );
        // Find the feedback with the matching id
        const item = allFeedback.find(
          (fb) => String(fb.id) === String(feedbackId)
        );
        if (!item) throw new Error("Feedback not found");
        setFeedback(item);
      } catch (err) {
        setError("Could not load feedback.");
      }
    };
    fetchFeedback();
  }, [feedbackId, isAdmin, navigate]);

  return (
    <div className="min-h-screen pb-20 bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white">
      <Container>
        <Title>🤖 AI Feedback {feedbackId}</Title>
        {error && <p className="text-red-500">{error}</p>}
        {!feedback ? (
          <p>Loading...</p>
        ) : (
          <Card>
            <h3 className="text-xl font-semibold">{feedback.title}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Added on {new Date(feedback.created_at).toLocaleString()}
            </p>
            <div className="mt-4">{feedback.content}</div>
          </Card>
        )}
        <div className="text-center mt-8">
          <Button
            variant="link"
            type="button"
            onClick={() => navigate("/ai-feedback")}
          >
            ⬅ Back to AI Feedback
          </Button>
        </div>
      </Container>
    </div>
  );
}

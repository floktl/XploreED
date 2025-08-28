import Modal from "../../../common/UI/Modal.jsx";
import ExerciseDetails from "./Components/ExerciseDetails";
import ReportForm from "./Forms/ReportForm";

interface Props {
    exercise: { id: number | string; question: string };
    userAnswer: string;
    correctAnswer: string;
    onSend: (message: string) => Promise<void>;
    onClose: () => void;
}

export default function ReportExerciseModal({
    exercise,
    userAnswer,
    correctAnswer,
    onSend,
    onClose,
}: Props) {
    return (
        <Modal onClose={onClose}>
            <h2 className="text-lg font-bold mb-2">Report Exercise Error</h2>

            <ExerciseDetails
                exercise={exercise}
                userAnswer={userAnswer}
                correctAnswer={correctAnswer}
            />

            <ReportForm
                onSend={onSend}
                onCancel={onClose}
            />
        </Modal>
    );
}

import { Container } from "../../../common/UI/UI";
import Card from "../../../common/UI/Card";
import Button from "../../../common/UI/Button";
import Footer from "../../../common/UI/Footer";
import { CheckCircle, XCircle } from "lucide-react";
import LevelUpTestHeader from "./LevelUpTestHeader";

export default function LevelUpTestResult({ result, onNavigate, darkMode }) {
  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container className="pb-20"
        bottom={
          <Button variant="primary" onClick={() => onNavigate("/menu")}>Back</Button>
        }
      >
        <LevelUpTestHeader title="Progress Test Result" />
        <Card className="text-center py-6 flex items-center justify-center gap-2">
          {result ? (
            <>
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span>You passed the test!</span>
            </>
          ) : (
            <>
              <XCircle className="w-5 h-5 text-red-600" />
              <span>You did not pass.</span>
            </>
          )}
        </Card>
      </Container>
      <Footer>
        <Button
          variant="primary"
          size="sm"
          className="rounded-full"
          onClick={() => onNavigate("/menu")}
        >
          Back
        </Button>
      </Footer>
    </div>
  );
}

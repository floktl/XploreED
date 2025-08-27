import React from "react";
import { ArrowLeft } from "lucide-react";
import Button from "../UI/Button";
import Footer from "../UI/Footer";

export default function AIFeedbackFooter({ onNavigate, actions }) {
  return (
    <Footer>
      <div className="flex gap-2">
        <Button
          size="sm"
          variant="ghost"
          type="button"
          onClick={() => onNavigate("/menu")}
          className="gap-2 rounded-full"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </Button>
        {actions}
      </div>
    </Footer>
  );
}

import React from "react";
import { XCircle, ArrowLeft } from "lucide-react";
import Button from "../UI/Button";
import Footer from "../UI/Footer";

export default function SettingsFooter({ onNavigate, onShowDelete }) {
  return (
    <Footer>
      <Button
        size="md"
        variant="ghost"
        type="button"
        onClick={() => onNavigate("/profile")}
        className="gap-2"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </Button>
      <Button
        variant="danger"
        onClick={onShowDelete}
        className="gap-2"
      >
        <XCircle className="w-4 h-4" />
        Delete Account
      </Button>
    </Footer>
  );
}

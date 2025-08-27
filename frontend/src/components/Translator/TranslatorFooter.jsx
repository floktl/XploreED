import React from "react";
import { ArrowLeft } from "lucide-react";
import Button from "../UI/Button";
import Footer from "../UI/Footer";

export default function TranslatorFooter({ onNavigate }) {
  return (
    <Footer>
      <Button size="md" variant="ghost" type="button" onClick={() => onNavigate("/menu")} className="gap-2">
        <ArrowLeft className="w-4 h-4" />
        Back
      </Button>
    </Footer>
  );
}

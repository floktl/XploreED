import React from "react";
import { ArrowLeft } from "lucide-react";
import Button from "../UI/Button";
import Footer from "../UI/Footer";

export default function ProfileStatsFooter({ onNavigate }) {
  return (
    <Footer>
      <Button onClick={() => onNavigate("/admin-panel")} variant="link" className="gap-2">
        <ArrowLeft className="w-4 h-4" />
        Back to Admin Panel
      </Button>
    </Footer>
  );
}

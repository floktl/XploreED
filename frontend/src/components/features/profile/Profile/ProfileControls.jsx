import { Settings, Sun, Moon } from "lucide-react";
import Button from "../../../common/UI/Button";

export default function ProfileControls({ onNavigate, onToggleDarkMode, darkMode }) {
  return (
    <div className="mt-6 flex justify-center gap-4">
      <Button onClick={() => onNavigate("/settings")} className="gap-2">
        <Settings className="w-4 h-4" />
        Settings
      </Button>
      <Button variant="secondary" onClick={onToggleDarkMode} className="gap-2">
        {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        {darkMode ? "Light" : "Dark"}
      </Button>
    </div>
  );
}

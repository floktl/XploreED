import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";
import { Book, Target, BrainCircuit, User, Settings, Sun, Moon, ArrowLeft } from "lucide-react";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Badge from "./UI/Badge";
import Footer from "./UI/Footer";
import { getMe, getRole, fetchProfileResults } from "../api";
import useAppStore from "../store/useAppStore";

export default function Profile() {
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  const username = useAppStore((state) => state.username);
  const setUsername = useAppStore((state) => state.setUsername);
  const isAdmin = useAppStore((state) => state.isAdmin);
  const setIsAdmin = useAppStore((state) => state.setIsAdmin);
  const navigate = useNavigate();
  const darkMode = useAppStore((state) => state.darkMode);
  const toggleDarkMode = useAppStore((state) => state.toggleDarkMode);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const data = await getMe();
        setUsername(data.username);

        const roleData = await getRole();
        setIsAdmin(roleData.is_admin);

        if (roleData.is_admin) {
          navigate("/admin-panel");
          return;
        }

        const profileResults = await fetchProfileResults();
        setResults(profileResults);
      } catch (err) {
        console.warn("[CLIENT] Not logged in or session expired.");
        navigate("/");
      }
    };

    checkSession();
  }, [navigate, setUsername, setIsAdmin]);

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container >
        <Title>
          <div className="flex items-center gap-2">
            <User className="w-6 h-6" />
            <span>Profile {username && `(${username})`}</span> <Badge type="default">Student</Badge>
          </div>
        </Title>
        <p className={`text-center mb-6 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>Your game results are listed below:</p>

        <Card className="mb-6">
          <div className="flex flex-col gap-4">
            <Button type="button" variant="primary" onClick={() => navigate("/vocabulary")} className="justify-start gap-3">
              <Book className="w-5 h-5" />
              My Vocabulary
            </Button>
            <Button type="button" variant="primary" onClick={() => navigate("/progress-test")} className="justify-start gap-3">
              <Target className="w-5 h-5" />
              Progress Test
            </Button>
            <Button type="button" variant="primary" onClick={() => navigate("/topic-memory")} className="justify-start gap-3">
              <BrainCircuit className="w-5 h-5" />
              Topic Memory
            </Button>
          </div>
        </Card>

        {error && <Alert type="error">{error}</Alert>}

        <div className="mt-6 flex justify-center gap-4">
          <Button onClick={() => navigate("/settings")} className="gap-2">
            <Settings className="w-4 h-4" />
            Settings
          </Button>
          <Button variant="secondary" onClick={toggleDarkMode} className="gap-2">
            {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            {darkMode ? "Light" : "Dark"}
          </Button>
        </div>
      </Container>

      <Footer>
        <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")} className="gap-2">
          <ArrowLeft className="w-4 h-4" />
          Back to Menu
        </Button>
      </Footer>
    </div>
  );
}

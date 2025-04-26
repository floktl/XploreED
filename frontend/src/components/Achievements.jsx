// Achievements.jsx
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Award } from "lucide-react";
import Button from "./UI/Button";
import { Title, Container } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Spinner from "./UI/Spinner";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";
import { getAchievements } from "../api";

// Helper function to format date
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

export default function Achievements() {
  const [achievements, setAchievements] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  const navigate = useNavigate();
  const username = useAppStore((state) => state.username);
  const darkMode = useAppStore((state) => state.darkMode);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await getAchievements();
        setAchievements(data);
        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch achievements:", err);
        setError("Could not load achievements. Please try again later.");
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Get requirement text
  const getRequirementText = (type, value) => {
    switch (type) {
      case 'translations':
        return `Complete ${value} translations`;
      case 'perfect_streak':
        return `Get ${value} perfect translations in a row`;
      case 'streak':
        return `Maintain a ${value}-day learning streak`;
      case 'lessons':
        return `Complete ${value} lessons`;
      case 'pronunciation':
        return `Practice pronunciation ${value} times`;
      default:
        return `Requirement: ${type} (${value})`;
    }
  };

  // Get progress percentage
  const getProgressPercentage = (achievement) => {
    // This is a placeholder - in a real app, you would calculate actual progress
    return Math.floor(Math.random() * 100);
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>
          <Award className="inline-block mr-2 w-6 h-6" />
          Achievements
        </Title>

        {error && <Alert type="error">{error}</Alert>}

        {loading ? (
          <div className="flex justify-center my-12">
            <Spinner />
          </div>
        ) : (
          <>
            {achievements && (
              <>
                {/* Earned Achievements */}
                <h2 className={`text-xl font-semibold mb-4 ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
                  Earned Achievements
                </h2>
                
                {achievements.earned.length === 0 ? (
                  <Card className="mb-6">
                    <p className={`text-center py-4 ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                      You haven't earned any achievements yet. Keep learning to unlock them!
                    </p>
                  </Card>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    {achievements.earned.map((achievement) => (
                      <Card key={achievement.id}>
                        <div className="flex items-center">
                          <div className="text-4xl mr-4">{achievement.icon}</div>
                          <div>
                            <h3 className={`font-bold ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
                              {achievement.name}
                            </h3>
                            <p className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                              {achievement.description}
                            </p>
                            <p className={`text-xs mt-1 ${darkMode ? "text-gray-500" : "text-gray-500"}`}>
                              Earned on {formatDate(achievement.earned_date)}
                            </p>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
                
                {/* Available Achievements */}
                <h2 className={`text-xl font-semibold mb-4 ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
                  Available Achievements
                </h2>
                
                {achievements.available.length === 0 ? (
                  <Card>
                    <p className={`text-center py-4 ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                      Congratulations! You've earned all available achievements.
                    </p>
                  </Card>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {achievements.available.map((achievement) => {
                      const progress = getProgressPercentage(achievement);
                      
                      return (
                        <Card key={achievement.id} className={darkMode ? "bg-gray-800" : "bg-gray-50"}>
                          <div className="flex items-center">
                            <div className={`text-4xl mr-4 ${darkMode ? "opacity-50" : "opacity-40"}`}>
                              {achievement.icon}
                            </div>
                            <div className="flex-1">
                              <h3 className={`font-bold ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
                                {achievement.name}
                              </h3>
                              <p className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                                {achievement.description}
                              </p>
                              <p className={`text-xs mt-1 ${darkMode ? "text-gray-500" : "text-gray-500"}`}>
                                {getRequirementText(achievement.requirement_type, achievement.requirement_value)}
                              </p>
                              
                              {/* Progress bar */}
                              <div className="mt-2">
                                <div className="flex justify-between text-xs mb-1">
                                  <span className={darkMode ? "text-gray-400" : "text-gray-600"}>Progress</span>
                                  <span className={darkMode ? "text-gray-400" : "text-gray-600"}>{progress}%</span>
                                </div>
                                <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded">
                                  <div
                                    className={`h-2 rounded ${darkMode ? "bg-blue-600" : "bg-blue-500"}`}
                                    style={{ width: `${progress}%` }}
                                  ></div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </>
            )}
          </>
        )}

        <div className="mt-6 text-center">
          <Button onClick={() => navigate("/analytics")} variant="link">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Analytics
          </Button>
        </div>
      </Container>
      <Footer />
    </div>
  );
}

// AnalyticsDashboard.jsx
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Calendar, Award, Flame, BarChart3, PieChart, Activity } from "lucide-react";
import Button from "./UI/Button";
import { Title, Container } from "./UI/UI";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Spinner from "./UI/Spinner";
import Footer from "./UI/Footer";
import useAppStore from "../store/useAppStore";
import { getAnalytics, getAchievements } from "../api";

// Activity type colors
const ACTIVITY_COLORS = {
  translation: {
    bg: "bg-blue-500",
    bgDark: "bg-blue-700",
    text: "text-blue-700",
    textDark: "text-blue-300",
  },
  pronunciation: {
    bg: "bg-green-500",
    bgDark: "bg-green-700",
    text: "text-green-700",
    textDark: "text-green-300",
  },
  lesson: {
    bg: "bg-purple-500",
    bgDark: "bg-purple-700",
    text: "text-purple-700",
    textDark: "text-purple-300",
  },
  game: {
    bg: "bg-yellow-500",
    bgDark: "bg-yellow-700",
    text: "text-yellow-700",
    textDark: "text-yellow-300",
  },
};

// Helper function to format date
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

export default function AnalyticsDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [achievements, setAchievements] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [timeRange, setTimeRange] = useState(30); // Default to 30 days
  
  const navigate = useNavigate();
  const username = useAppStore((state) => state.username);
  const darkMode = useAppStore((state) => state.darkMode);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const analyticsData = await getAnalytics(timeRange);
        setAnalytics(analyticsData);
        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch analytics:", err);
        setError("Could not load analytics data. Please try again later.");
        setLoading(false);
      }
    };

    fetchData();
  }, [timeRange]);

  // Calculate activity summary
  const getActivitySummary = () => {
    if (!analytics || !analytics.activities) return [];
    
    return Object.entries(analytics.activities).map(([type, data]) => ({
      type,
      total: data.total_attempts,
      correct: data.total_correct,
      accuracy: data.total_attempts > 0 
        ? Math.round((data.total_correct / data.total_attempts) * 100) 
        : 0,
      time: data.total_time,
    }));
  };

  // Get color for activity type
  const getActivityColor = (type) => {
    return ACTIVITY_COLORS[type] || {
      bg: "bg-gray-500",
      bgDark: "bg-gray-700",
      text: "text-gray-700",
      textDark: "text-gray-300",
    };
  };

  // Format time spent
  const formatTimeSpent = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  // Render activity chart
  const renderActivityChart = () => {
    if (!analytics || !analytics.activities) return null;
    
    const activitySummary = getActivitySummary();
    if (activitySummary.length === 0) return null;
    
    return (
      <div className="mt-6">
        <h3 className={`text-lg font-semibold mb-3 ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
          <Activity className="inline-block mr-2 w-5 h-5" />
          Activity Breakdown
        </h3>
        <div className="space-y-4">
          {activitySummary.map((activity) => (
            <div key={activity.type} className="space-y-2">
              <div className="flex justify-between items-center">
                <span className={`font-medium capitalize ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
                  {activity.type}
                </span>
                <span className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                  {activity.correct}/{activity.total} ({activity.accuracy}%)
                </span>
              </div>
              <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded">
                <div
                  className={`h-2 rounded ${darkMode ? getActivityColor(activity.type).bgDark : getActivityColor(activity.type).bg}`}
                  style={{ width: `${activity.accuracy}%` }}
                ></div>
              </div>
              <div className="flex justify-between text-xs">
                <span className={darkMode ? "text-gray-400" : "text-gray-600"}>
                  Total attempts: {activity.total}
                </span>
                <span className={darkMode ? "text-gray-400" : "text-gray-600"}>
                  Time spent: {formatTimeSpent(activity.time)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render daily activity heatmap
  const renderDailyActivity = () => {
    if (!analytics || !analytics.dates) return null;
    
    const today = new Date();
    const dates = analytics.dates;
    
    // Group dates by week
    const weeks = [];
    let currentWeek = [];
    
    for (let i = 0; i < dates.length; i++) {
      const date = new Date(dates[i]);
      const dayOfWeek = date.getDay();
      
      if (dayOfWeek === 0 && currentWeek.length > 0) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
      
      currentWeek.push(dates[i]);
      
      if (i === dates.length - 1) {
        weeks.push(currentWeek);
      }
    }
    
    // Calculate activity level for each date
    const getActivityLevel = (date) => {
      let totalActivity = 0;
      
      Object.values(analytics.activities).forEach(activity => {
        if (activity.daily[date]) {
          totalActivity += activity.daily[date].attempts;
        }
      });
      
      if (totalActivity === 0) return 0;
      if (totalActivity <= 2) return 1;
      if (totalActivity <= 5) return 2;
      if (totalActivity <= 10) return 3;
      return 4;
    };
    
    // Get color for activity level
    const getActivityLevelColor = (level) => {
      if (level === 0) return darkMode ? "bg-gray-800" : "bg-gray-200";
      if (level === 1) return darkMode ? "bg-green-900" : "bg-green-200";
      if (level === 2) return darkMode ? "bg-green-800" : "bg-green-300";
      if (level === 3) return darkMode ? "bg-green-700" : "bg-green-400";
      return darkMode ? "bg-green-600" : "bg-green-500";
    };
    
    return (
      <div className="mt-6">
        <h3 className={`text-lg font-semibold mb-3 ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
          <Calendar className="inline-block mr-2 w-5 h-5" />
          Daily Activity
        </h3>
        <div className="overflow-x-auto">
          <div className="min-w-max">
            <div className="flex text-xs mb-1">
              <div className="w-8"></div>
              <div className="flex space-x-1">
                <div className="w-6 text-center">S</div>
                <div className="w-6 text-center">M</div>
                <div className="w-6 text-center">T</div>
                <div className="w-6 text-center">W</div>
                <div className="w-6 text-center">T</div>
                <div className="w-6 text-center">F</div>
                <div className="w-6 text-center">S</div>
              </div>
            </div>
            {weeks.map((week, weekIndex) => (
              <div key={weekIndex} className="flex items-center mb-1">
                <div className="w-8 text-xs text-right pr-2">
                  {new Date(week[0]).toLocaleDateString(undefined, { month: 'short' })}
                </div>
                <div className="flex space-x-1">
                  {Array.from({ length: 7 }).map((_, dayIndex) => {
                    const dateIndex = week.findIndex(date => new Date(date).getDay() === dayIndex);
                    const date = dateIndex >= 0 ? week[dateIndex] : null;
                    const level = date ? getActivityLevel(date) : 0;
                    
                    return (
                      <div
                        key={dayIndex}
                        className={`w-6 h-6 rounded-sm ${getActivityLevelColor(level)}`}
                        title={date ? `${formatDate(date)}: ${level > 0 ? 'Activity level ' + level : 'No activity'}` : ''}
                      ></div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="flex justify-center mt-2 text-xs">
          <div className="flex items-center space-x-1">
            <div className={`w-3 h-3 rounded-sm ${darkMode ? "bg-gray-800" : "bg-gray-200"}`}></div>
            <span className={darkMode ? "text-gray-400" : "text-gray-600"}>None</span>
          </div>
          <div className="mx-2">→</div>
          <div className="flex items-center space-x-1">
            <div className={`w-3 h-3 rounded-sm ${darkMode ? "bg-green-600" : "bg-green-500"}`}></div>
            <span className={darkMode ? "text-gray-400" : "text-gray-600"}>High</span>
          </div>
        </div>
      </div>
    );
  };

  // Render streak information
  const renderStreak = () => {
    if (!analytics || !analytics.streak) return null;
    
    const { current, longest, start_date } = analytics.streak;
    
    return (
      <div className="mt-6">
        <h3 className={`text-lg font-semibold mb-3 ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
          <Flame className="inline-block mr-2 w-5 h-5" />
          Learning Streak
        </h3>
        <div className="flex space-x-4">
          <div className={`flex-1 p-4 rounded-lg ${darkMode ? "bg-gray-800" : "bg-blue-50"}`}>
            <div className="text-center">
              <div className={`text-3xl font-bold ${darkMode ? "text-blue-400" : "text-blue-600"}`}>
                {current}
              </div>
              <div className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                Current Streak
              </div>
              {start_date && (
                <div className={`text-xs mt-1 ${darkMode ? "text-gray-500" : "text-gray-500"}`}>
                  Since {formatDate(start_date)}
                </div>
              )}
            </div>
          </div>
          <div className={`flex-1 p-4 rounded-lg ${darkMode ? "bg-gray-800" : "bg-purple-50"}`}>
            <div className="text-center">
              <div className={`text-3xl font-bold ${darkMode ? "text-purple-400" : "text-purple-600"}`}>
                {longest}
              </div>
              <div className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                Longest Streak
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render achievements
  const renderAchievements = () => {
    if (!analytics || !analytics.achievements) return null;
    
    const { achievements, available_achievements } = analytics;
    
    return (
      <div className="mt-6">
        <h3 className={`text-lg font-semibold mb-3 ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
          <Award className="inline-block mr-2 w-5 h-5" />
          Achievements
        </h3>
        
        {achievements.length === 0 ? (
          <p className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
            No achievements earned yet. Keep learning to unlock achievements!
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {achievements.map((achievement) => (
              <div 
                key={achievement.id}
                className={`p-3 rounded-lg border ${
                  darkMode 
                    ? "bg-gray-800 border-gray-700" 
                    : "bg-white border-gray-200"
                }`}
              >
                <div className="flex items-center">
                  <div className="text-2xl mr-3">{achievement.icon}</div>
                  <div>
                    <div className={`font-medium ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
                      {achievement.name}
                    </div>
                    <div className={`text-xs ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                      {achievement.description}
                    </div>
                    <div className={`text-xs mt-1 ${darkMode ? "text-gray-500" : "text-gray-500"}`}>
                      Earned on {formatDate(achievement.earned_date)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        
        {available_achievements && available_achievements.length > 0 && (
          <div className="mt-4">
            <h4 className={`text-sm font-medium mb-2 ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
              Available Achievements
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {available_achievements.slice(0, 4).map((achievement) => (
                <div 
                  key={achievement.id}
                  className={`p-3 rounded-lg border ${
                    darkMode 
                      ? "bg-gray-800 border-gray-700 opacity-50" 
                      : "bg-gray-50 border-gray-200 opacity-75"
                  }`}
                >
                  <div className="flex items-center">
                    <div className="text-2xl mr-3">{achievement.icon}</div>
                    <div>
                      <div className={`font-medium ${darkMode ? "text-gray-300" : "text-gray-700"}`}>
                        {achievement.name}
                      </div>
                      <div className={`text-xs ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                        {achievement.description}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {available_achievements.length > 4 && (
              <div className="text-center mt-2">
                <span className={`text-xs ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                  +{available_achievements.length - 4} more achievements to unlock
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // Render overall stats
  const renderOverallStats = () => {
    if (!analytics || !analytics.totals) return null;
    
    const { correct, attempts, time_spent } = analytics.totals;
    const accuracy = attempts > 0 ? Math.round((correct / attempts) * 100) : 0;
    
    return (
      <div className="mt-6">
        <h3 className={`text-lg font-semibold mb-3 ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
          <BarChart3 className="inline-block mr-2 w-5 h-5" />
          Overall Statistics
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className={`p-3 rounded-lg ${darkMode ? "bg-gray-800" : "bg-blue-50"}`}>
            <div className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
              Total Activities
            </div>
            <div className={`text-2xl font-bold ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
              {attempts}
            </div>
          </div>
          <div className={`p-3 rounded-lg ${darkMode ? "bg-gray-800" : "bg-green-50"}`}>
            <div className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
              Correct
            </div>
            <div className={`text-2xl font-bold ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
              {correct}
            </div>
          </div>
          <div className={`p-3 rounded-lg ${darkMode ? "bg-gray-800" : "bg-yellow-50"}`}>
            <div className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
              Accuracy
            </div>
            <div className={`text-2xl font-bold ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
              {accuracy}%
            </div>
          </div>
          <div className={`p-3 rounded-lg ${darkMode ? "bg-gray-800" : "bg-purple-50"}`}>
            <div className={`text-sm ${darkMode ? "text-gray-400" : "text-gray-600"}`}>
              Time Spent
            </div>
            <div className={`text-2xl font-bold ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
              {formatTimeSpent(time_spent)}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
      <Container>
        <Title>📊 Learning Analytics</Title>
        
        {/* Time range selector */}
        <div className="flex justify-center mb-6">
          <div className="inline-flex rounded-md shadow-sm" role="group">
            <button
              onClick={() => setTimeRange(7)}
              className={`px-4 py-2 text-sm font-medium rounded-l-lg ${
                timeRange === 7
                  ? darkMode
                    ? "bg-blue-600 text-white"
                    : "bg-blue-500 text-white"
                  : darkMode
                  ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              7 Days
            </button>
            <button
              onClick={() => setTimeRange(30)}
              className={`px-4 py-2 text-sm font-medium ${
                timeRange === 30
                  ? darkMode
                    ? "bg-blue-600 text-white"
                    : "bg-blue-500 text-white"
                  : darkMode
                  ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              30 Days
            </button>
            <button
              onClick={() => setTimeRange(90)}
              className={`px-4 py-2 text-sm font-medium rounded-r-lg ${
                timeRange === 90
                  ? darkMode
                    ? "bg-blue-600 text-white"
                    : "bg-blue-500 text-white"
                  : darkMode
                  ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              90 Days
            </button>
          </div>
        </div>

        {error && <Alert type="error">{error}</Alert>}

        {loading ? (
          <div className="flex justify-center my-12">
            <Spinner />
          </div>
        ) : (
          <Card>
            {analytics && analytics.totals && analytics.totals.attempts === 0 ? (
              <div className="text-center py-8">
                <h3 className={`text-xl font-semibold mb-2 ${darkMode ? "text-gray-200" : "text-gray-800"}`}>
                  No activity data yet
                </h3>
                <p className={`${darkMode ? "text-gray-400" : "text-gray-600"}`}>
                  Start learning German to see your progress analytics!
                </p>
                <Button 
                  variant="primary" 
                  className="mt-4"
                  onClick={() => navigate("/translate")}
                >
                  Start Learning
                </Button>
              </div>
            ) : (
              <>
                {renderOverallStats()}
                {renderStreak()}
                {renderActivityChart()}
                {renderDailyActivity()}
                {renderAchievements()}
              </>
            )}
          </Card>
        )}

        <div className="mt-6 text-center">
          <Button onClick={() => navigate("/menu")} variant="link">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Menu
          </Button>
        </div>
      </Container>
      <Footer />
    </div>
  );
}

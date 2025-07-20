const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

// ---------- Auth ----------
export const signup = async (username, password) => {
  const res = await fetch(`${BASE_URL}/api/signup`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  try {
    return await res.json();
  } catch {
    return { error: "❌ Invalid signup response from server" };
  }
};

export const login = async (username, password) => {
  const res = await fetch(`${BASE_URL}/api/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  try {
    return await res.json();
  } catch {
    return { error: "❌ Invalid login response from server" };
  }
};

export const logout = async () => {
  const res = await fetch(`${BASE_URL}/api/logout`, {
    method: "POST",
    credentials: "include",
  });

  try {
    return await res.json();
  } catch {
    return { error: "❌ Logout failed" };
  }
};

// ---------- Profile ----------
export const getMe = async () => {
  const res = await fetch(`${BASE_URL}/api/me`, {
    credentials: "include",
  });
  if (!res.ok) {
    console.warn(`[API] getMe failed with status ${res.status}`);
    throw new Error("unauthorized");
  }
  return await res.json();
};

export const getRole = async () => {
  const res = await fetch(`${BASE_URL}/api/role`, {
    credentials: "include",
  });
  if (!res.ok) {
    console.warn(`[API] getRole failed with status ${res.status}`);
    throw new Error("unauthorized");
  }
  return await res.json();
};

export const fetchProfileResults = async () => {
  const res = await fetch(`${BASE_URL}/api/profile`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch profile");
  return await res.json();
};

export const getProfile = async () => {
  const res = await fetch(`${BASE_URL}/api/profile`, {
    method: "GET",
    credentials: "include",
  });

  try {
    return await res.json();
  } catch {
    return { error: "❌ Profile response invalid" };
  }
};

export const getUserLevel = async () => {
  const res = await fetch(`${BASE_URL}/api/user-level`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch user level");
  return await res.json();
};

export const setUserLevel = async (level) => {
  const res = await fetch(`${BASE_URL}/api/user-level`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level }),
  });
  return await res.json();
};

export async function getUserResults() {
  const res = await fetch(`${BASE_URL}/api/profile`, {
    credentials: "include",
  });
  return res.json();
}

export async function fetchProfileStats(username) {
  const res = await fetch(`${BASE_URL}/api/admin/profile-stats`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  });

  if (!res.ok) {
    throw new Error("❌ Failed to load user stats");
  }

  return await res.json();
}

// ---------- Vocabulary ----------
export async function getVocabulary() {
  const res = await fetch(`${BASE_URL}/api/vocabulary`, {
    credentials: "include",
  });
  return res.json();
}

export const getNextVocabCard = async () => {
  const res = await fetch(`${BASE_URL}/api/vocab-train`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch card");
  return res.json();
};

export const submitVocabAnswer = async (id, quality) => {
  const res = await fetch(`${BASE_URL}/api/vocab-train`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ id, quality }),
  });
  if (!res.ok) throw new Error("Failed to submit answer");
  return res.json();
};

export const saveVocabWords = async (words) => {
  const res = await fetch(`${BASE_URL}/api/save-vocab`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ words }),
  });
  if (!res.ok) throw new Error("Failed to save vocab");
  return res.json();
};

export const deleteVocab = async (id) => {
  const res = await fetch(`${BASE_URL}/api/vocabulary/${id}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to delete vocab");
  return res.json();
};

export const reportVocab = async (id, message) => {
  const res = await fetch(`${BASE_URL}/api/vocabulary/${id}/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error("Failed to send report");
  return res.json();
};

// ---------- Topic Memory ----------
export async function getTopicMemory() {
  const res = await fetch(`${BASE_URL}/api/topic-memory`, {
    credentials: "include",
  });
  return res.json();
}

export async function clearTopicMemory() {
  const res = await fetch(`${BASE_URL}/api/topic-memory`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to clear topic memory");
  return res.json();
}

export async function getTopicWeaknesses() {
  const res = await fetch(`${BASE_URL}/api/topic-weaknesses`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch topic weaknesses");
  return res.json();
}

// ---------- Game ----------
export async function getLevel(level) {
  const res = await fetch(`${BASE_URL}/api/level`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level }),
  });
  return res.json();
}

export async function fetchLevelData(level) {
  try {
    const res = await fetch(`${BASE_URL}/api/level`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level }),
    });

    const data = await res.json();
    return {
      scrambled: Array.isArray(data.scrambled) ? data.scrambled : [],
      sentence: data.sentence || "",
    };
  } catch (err) {
    console.error("[API] Failed to fetch level data:", err);
    return { scrambled: [] };
  }
}

export async function submitLevel(payload) {
  const res = await fetch(`${BASE_URL}/api/level/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function submitLevelAnswer(level, answer, sentence = "") {
  const res = await fetch(`${BASE_URL}/api/level/submit`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level, answer, sentence }),
  });

  return await res.json();
}

// ---------- Translation ----------
export async function translateSentence(payload) {
  // Step 1: Start translation job
  const res = await fetch(`${BASE_URL}/api/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorText = await res.text();
    console.error("[API] Server error response:", errorText);
    throw new Error(`❌ Server error: ${res.status}`);
  }
  const { job_id } = await res.json();
  if (!job_id) throw new Error("❌ No job_id returned from server");

  // Step 2: Poll for result
  const poll = async (retries = 0) => {
    const statusRes = await fetch(
      `${BASE_URL}/api/translate/status/${job_id}`,
      {
        credentials: "include",
      },
    );
    if (!statusRes.ok) throw new Error("❌ Failed to poll translation status");
    const data = await statusRes.json();
    if (data.status === "done") return data.result;
    if (data.status === "not_found")
      throw new Error("❌ Translation job not found");
    if (retries > 30) throw new Error("❌ Translation timed out");
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return poll(retries + 1);
  };
  return poll();
}

export async function translateSentenceStream(payload, onChunk) {
  const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
  const res = await fetch(`${BASE_URL}/api/translate/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!res.ok || !res.body) throw new Error("Failed to connect to stream");
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let lines = buffer.split(/\n\n/);
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const chunk = line.replace(/^data: /, "");
        if (onChunk) onChunk(chunk);
      }
    }
  }
  if (buffer && buffer.startsWith("data: ")) {
    const chunk = buffer.replace(/^data: /, "");
    if (onChunk) onChunk(chunk);
  }
}

// ---------- Admin ----------

export async function verifyAdminPassword(password) {
  try {
    const res = await fetch(`${BASE_URL}/api/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ password }),
    });

    if (!res.ok) {
      console.warn("[API] Invalid response status:", res.status);
      return false;
    }

    const data = await res.json();
    return data.msg === "Login successful"; // ✅ this matches your Flask response
  } catch (err) {
    console.error("[API] Admin login failed:", err);
    return false;
  }
}

// ---------- Admin ----------
export const getAdminRole = async () =>
  fetch(`${BASE_URL}/api/role`, { credentials: "include" }).then((res) =>
    res.json(),
  );

export const getAdminResults = async () =>
  fetch(`${BASE_URL}/api/admin/results`, { credentials: "include" }).then(
    (res) => res.json(),
  );

export const getLessonProgressSummary = async () =>
  fetch(`${BASE_URL}/api/admin/lesson-progress-summary`, {
    credentials: "include",
  }).then((res) => res.json());

export const saveLesson = async (lesson, isEdit = false) => {
  const url = isEdit
    ? `${BASE_URL}/api/admin/lesson-content/${lesson.lesson_id}`
    : `${BASE_URL}/api/admin/lesson-content`;

  const method = isEdit ? "PUT" : "POST";

  return fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(lesson),
  });
};

export async function togglePublishLesson(lessonId, updatedLesson) {
  return await fetch(`${BASE_URL}/api/admin/lesson-content/${lessonId}`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updatedLesson),
  });
}

// Get detailed lesson progress
export const getLessonProgressDetails = async (lessonId) => {
  const res = await fetch(`${BASE_URL}/api/admin/lesson-progress/${lessonId}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch progress details");
  return await res.json();
};

// Update publish state
export const updateLessonPublished = async (lessonId, publish) => {
  const res = await fetch(`${BASE_URL}/api/admin/lesson-content/${lessonId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ published: publish ? 1 : 0 }),
  });
  return res.ok;
};

// Delete a lesson
export const deleteLesson = async (lessonId) => {
  const res = await fetch(`${BASE_URL}/api/admin/lesson-content/${lessonId}`, {
    method: "DELETE",
    credentials: "include",
  });
  return res.ok;
};

// -------- Users --------
export const fetchUsers = async () => {
  const res = await fetch(`${BASE_URL}/api/admin/users`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch users");
  return res.json();
};

export const updateUserAccount = async (username, payload) => {
  const res = await fetch(
    `${BASE_URL}/api/admin/users/${encodeURIComponent(username)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    },
  );
  return res.json();
};

export const deleteUserAccount = async (username) => {
  const res = await fetch(
    `${BASE_URL}/api/admin/users/${encodeURIComponent(username)}`,
    {
      method: "DELETE",
      credentials: "include",
    },
  );
  return res.json();
};

// Refresh lessons
export const getLessons = async () => {
  const res = await fetch(`${BASE_URL}/api/admin/lesson-content`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch lessons");
  return await res.json();
};

//----------------Lesson-edit------------
export const getLessonById = async (lessonId) => {
  const res = await fetch(`${BASE_URL}/api/admin/lesson-content/${lessonId}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch lesson");
  return await res.json();
};

export const updateLesson = async (lessonId, lessonData) => {
  return await fetch(`${BASE_URL}/api/admin/lesson-content/${lessonId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(lessonData),
  });
};

//----------------Lessons------------
export const getStudentLessons = async () => {
  const res = await fetch(`${BASE_URL}/api/lessons`, {
    method: "GET",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch lessons");
  return await res.json();
};

export async function updatePassword(current_password, new_password) {
  const res = await fetch(`${BASE_URL}/api/settings/password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ current_password, new_password }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.error);
  return data;
}

export async function deactivateAccount(deleteAll = false) {
  const res = await fetch(`${BASE_URL}/api/settings/deactivate`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ delete_all: deleteAll }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.error);
  return data;
}

export const getLesson = async (lessonId) => {
  const res = await fetch(`${BASE_URL}/api/lesson/${lessonId}`, {
    method: "GET",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch lesson content");
  return res.json();
};

export const getLessonProgress = async (lessonId) => {
  const res = await fetch(`${BASE_URL}/api/lesson-progress/${lessonId}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch progress");
  return res.json();
};

export const isLessonCompleted = async (lessonId) => {
  const res = await fetch(`${BASE_URL}/api/lesson-completed`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ lesson_id: parseInt(lessonId) }),
  });
  if (!res.ok) throw new Error("Failed to check completion status");
  return res.json();
};

export const markLessonComplete = async (lessonId) => {
  const res = await fetch(`${BASE_URL}/api/mark-as-completed`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ lesson_id: parseInt(lessonId) }),
  });
  if (!res.ok) throw new Error("Failed to mark lesson as complete");
  return res.json();
};

export const updateLessonBlockProgress = async (
  lessonId,
  blockId,
  completed,
) => {
  const res = await fetch(`${BASE_URL}/api/lesson-progress`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      lesson_id: parseInt(lessonId),
      block_id: blockId,
      completed,
    }),
  });
  if (!res.ok) throw new Error("Failed to update block progress");
  return res.json();
};

export const getAiExercises = async (payload = {}) => {
  const res = await fetch(`${BASE_URL}/api/ai-exercises`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to fetch AI exercises");
  return res.json();
};

export const getTrainingExercises = async (payload = {}) => {
  const res = await fetch(`${BASE_URL}/api/training-exercises`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to fetch training exercises");
  return res.json();
};

export const sendSupportFeedback = async (message) => {
  const res = await fetch(`${BASE_URL}/api/support/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error("Failed to send feedback");
  return res.json();
};

export const fetchSupportFeedback = async () => {
  const res = await fetch(`${BASE_URL}/api/support/feedback`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch feedback");
  return res.json();
};

export const getAiFeedback = async () => {
  const res = await fetch(`${BASE_URL}/api/ai-feedback`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch AI feedback");
  return res.json();
};

export const getAiFeedbackItem = async (feedbackId) => {
  const res = await fetch(`${BASE_URL}/api/ai-feedback/${feedbackId}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch AI feedback item");
  return res.json();
};

export const generateAiFeedback = async (payload = {}) => {
  const res = await fetch(`${BASE_URL}/api/ai-feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to generate AI feedback");
  return res.json();
};

// New progress tracking functions for AI feedback
export const generateAiFeedbackWithProgress = async (payload = {}) => {
  const res = await fetch(
    `${BASE_URL}/api/ai-feedback/generate-with-progress`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    },
  );
  if (!res.ok) throw new Error("Failed to start AI feedback generation");
  return res.json();
};

export const getFeedbackProgress = async (sessionId) => {
  const res = await fetch(`${BASE_URL}/api/ai-feedback/progress/${sessionId}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to get feedback progress");
  return res.json();
};

export const getFeedbackResult = async (sessionId) => {
  const res = await fetch(`${BASE_URL}/api/ai-feedback/result/${sessionId}`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to get feedback result");
  return res.json();
};

export const submitExerciseAnswers = async (
  blockId,
  answers = {},
  exerciseBlock = null,
) => {
  console.log(`[API] submitExerciseAnswers called for block ${blockId}`);
  const startTime = Date.now();

  const res = await fetch(`${BASE_URL}/api/ai-exercise/${blockId}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      answers,
      exercise_block: exerciseBlock || { exercises: [] },
    }),
  });

  const endTime = Date.now();
  console.log(`[API] submitExerciseAnswers completed in ${endTime - startTime}ms`);

  if (!res.ok) throw new Error("Failed to submit answers");
  return res.json();
};

export const argueExerciseAnswers = async (
  blockId,
  answers = {},
  exerciseBlock = null,
) => {
  const res = await fetch(`${BASE_URL}/api/ai-exercise/${blockId}/argue`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      answers,
      exercise_block: exerciseBlock || { exercises: [] },
    }),
  });
  if (!res.ok) throw new Error("Failed to argue answers");
  return res.json();
};

export const getAiLesson = async () => {
  const res = await fetch(`${BASE_URL}/api/ai-lesson`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch AI lesson");
  return res.text();
};

export const getWeaknessLesson = async () => {
  const res = await fetch(`${BASE_URL}/api/weakness-lesson`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch AI lesson");
  return res.text();
};

export const getReadingExercise = async (style = "story") => {
  const res = await fetch(`${BASE_URL}/api/reading-exercise`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ style }),
  });
  if (!res.ok) throw new Error("Failed to fetch reading exercise");
  return res.json();
};

export const submitReadingAnswers = async (
  answers = {},
  exercise_id = null,
) => {
  const res = await fetch(`${BASE_URL}/api/reading-exercise/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ answers, exercise_id }),
  });
  if (!res.ok) throw new Error("Failed to submit answers");
  return res.json();
};

export const getProgressTest = async () => {
  const res = await fetch(`${BASE_URL}/api/progress-test`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch progress test");
  return res.json();
};

export const submitProgressTest = async (payload) => {
  const res = await fetch(`${BASE_URL}/api/progress-test/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to submit progress test");
  return res.json();
};

export const askAiQuestion = async (question) => {
  const res = await fetch(`${BASE_URL}/api/ask-ai`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error("Failed to get AI answer");
  return res.json();
};

// Get Mistral chat history
export const getMistralChatHistory = async () => {
  const res = await fetch(`${BASE_URL}/api/mistral-chat-history`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to fetch chat history");
  return res.json();
};

// Add to Mistral chat history
export const addMistralChatHistory = async (question, answer) => {
  const res = await fetch(`${BASE_URL}/api/mistral-chat-history`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ question, answer }),
  });
  if (!res.ok) throw new Error("Failed to save chat history");
  return res.json();
};

export const deleteAllVocab = async () => {
  const res = await fetch(`${BASE_URL}/api/vocabulary`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to delete all vocab");
  return res.json();
};

export const getEnhancedResults = async (blockId) => {
    try {
        const response = await fetch(`${BASE_URL}/api/ai-exercise/${blockId}/results`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
            credentials: "include",
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Failed to fetch enhanced results:", error);
        throw error;
    }
};
